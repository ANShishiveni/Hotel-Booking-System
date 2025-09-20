"""
Booking routes with concurrency controls and timezone-aware logic
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, limiter
from app.models.user import User
from app.models.hotel import Hotel, Room, RoomType
from app.models.booking import Booking, BookingRoom, Guest
from app.services.booking_service import BookingService
from app.utils.decorators import validate_json, require_permissions
from app.utils.timezone_utils import convert_to_utc, get_user_timezone
from app.utils.validators import validate_booking_dates, validate_occupancy
from datetime import datetime, timedelta
from decimal import Decimal
import pytz

bookings_bp = Blueprint('bookings', __name__)

@bookings_bp.route('/search', methods=['GET'])
@limiter.limit("30 per minute")
def search_availability():
    """Search for available rooms"""
    try:
        # Get search parameters
        hotel_id = request.args.get('hotel_id', type=int)
        check_in = request.args.get('check_in')
        check_out = request.args.get('check_out')
        adults = request.args.get('adults', 1, type=int)
        children = request.args.get('children', 0, type=int)
        
        # Validate required parameters
        if not all([hotel_id, check_in, check_out]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Validate dates
        date_error = validate_booking_dates(check_in, check_out)
        if date_error:
            return jsonify({'error': date_error}), 400
        
        # Validate occupancy
        occupancy_error = validate_occupancy(adults, children)
        if occupancy_error:
            return jsonify({'error': occupancy_error}), 400
        
        # Convert dates to datetime objects
        check_in_dt = datetime.strptime(check_in, '%Y-%m-%d')
        check_out_dt = datetime.strptime(check_out, '%Y-%m-%d')
        
        # Search for available rooms
        booking_service = BookingService()
        available_rooms = booking_service.search_available_rooms(
            hotel_id=hotel_id,
            check_in=check_in_dt,
            check_out=check_out_dt,
            adults=adults,
            children=children
        )
        
        # Calculate pricing for each room type
        results = []
        for room_type in available_rooms:
            rate = room_type.calculate_price(check_in, check_out, adults, children)
            total_nights = (check_out_dt - check_in_dt).days
            total_amount = rate * total_nights
            
            results.append({
                'room_type_id': room_type.id,
                'name': room_type.name,
                'description': room_type.description,
                'max_occupancy': room_type.max_occupancy,
                'amenities': room_type.amenities,
                'rate_per_night': float(rate),
                'total_nights': total_nights,
                'total_amount': float(total_amount),
                'available_rooms': available_rooms[room_type]
            })
        
        return jsonify({
            'search_results': results,
            'search_params': {
                'hotel_id': hotel_id,
                'check_in': check_in,
                'check_out': check_out,
                'adults': adults,
                'children': children
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Search error: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500

@bookings_bp.route('/create', methods=['POST'])
@jwt_required()
@limiter.limit("5 per minute")
@validate_json(['hotel_id', 'check_in', 'check_out', 'adults', 'room_selections', 'guest_info'])
def create_booking():
    """Create a new booking with concurrency controls"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Validate booking data
        date_error = validate_booking_dates(data['check_in'], data['check_out'])
        if date_error:
            return jsonify({'error': date_error}), 400
        
        occupancy_error = validate_occupancy(data['adults'], data.get('children', 0))
        if occupancy_error:
            return jsonify({'error': occupancy_error}), 400
        
        # Convert dates to datetime objects
        check_in_dt = datetime.strptime(data['check_in'], '%Y-%m-%d')
        check_out_dt = datetime.strptime(data['check_out'], '%Y-%m-%d')
        
        # Get user timezone
        user_timezone = get_user_timezone(request)
        
        # Create or find guest
        guest = _create_or_find_guest(data['guest_info'])
        
        # Use booking service with transaction
        booking_service = BookingService()
        booking = booking_service.create_booking(
            user_id=current_user_id,
            hotel_id=data['hotel_id'],
            guest_id=guest.id,
            check_in=check_in_dt,
            check_out=check_out_dt,
            adults=data['adults'],
            children=data.get('children', 0),
            room_selections=data['room_selections'],
            special_requests=data.get('special_requests'),
            timezone=user_timezone
        )
        
        return jsonify({
            'message': 'Booking created successfully',
            'booking': booking.to_dict(include_rooms=True)
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Booking creation error: {str(e)}")
        return jsonify({'error': 'Booking creation failed'}), 500

@bookings_bp.route('/', methods=['GET'])
@jwt_required()
def get_user_bookings():
    """Get bookings for current user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get query parameters
        status = request.args.get('status')
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = Booking.query.filter_by(user_id=current_user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        # Order by creation date (newest first)
        query = query.order_by(Booking.created_at.desc())
        
        # Apply pagination
        bookings = query.offset(offset).limit(limit).all()
        total = query.count()
        
        return jsonify({
            'bookings': [booking.to_dict(include_rooms=True) for booking in bookings],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get bookings error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve bookings'}), 500

@bookings_bp.route('/<int:booking_id>', methods=['GET'])
@jwt_required()
def get_booking(booking_id):
    """Get specific booking details"""
    try:
        current_user_id = get_jwt_identity()
        
        booking = Booking.query.get_or_404(booking_id)
        
        # Check if user owns this booking or is admin
        if booking.user_id != current_user_id and not _is_admin(current_user_id):
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({
            'booking': booking.to_dict(include_rooms=True, include_payments=True)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get booking error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve booking'}), 500

@bookings_bp.route('/<int:booking_id>/cancel', methods=['POST'])
@jwt_required()
@validate_json(['reason'])
def cancel_booking(booking_id):
    """Cancel a booking"""
    try:
        current_user_id = get_jwt_identity()
        
        booking = Booking.query.get_or_404(booking_id)
        
        # Check if user owns this booking or is admin
        if booking.user_id != current_user_id and not _is_admin(current_user_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if booking can be cancelled
        if not booking.can_cancel:
            return jsonify({'error': 'Booking cannot be cancelled'}), 400
        
        # Use booking service to cancel
        booking_service = BookingService()
        booking_service.cancel_booking(booking_id, request.get_json().get('reason'))
        
        return jsonify({
            'message': 'Booking cancelled successfully',
            'booking': booking.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Cancel booking error: {str(e)}")
        return jsonify({'error': 'Booking cancellation failed'}), 500

@bookings_bp.route('/<int:booking_id>/checkin', methods=['POST'])
@jwt_required()
@require_permissions(['admin_all'])
def checkin_booking(booking_id):
    """Check-in a booking (admin only)"""
    try:
        booking = Booking.query.get_or_404(booking_id)
        
        if booking.status != 'confirmed':
            return jsonify({'error': 'Only confirmed bookings can be checked in'}), 400
        
        # Use booking service to check-in
        booking_service = BookingService()
        booking_service.checkin_booking(booking_id)
        
        return jsonify({
            'message': 'Check-in successful',
            'booking': booking.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Check-in error: {str(e)}")
        return jsonify({'error': 'Check-in failed'}), 500

@bookings_bp.route('/<int:booking_id>/checkout', methods=['POST'])
@jwt_required()
@require_permissions(['admin_all'])
def checkout_booking(booking_id):
    """Check-out a booking (admin only)"""
    try:
        booking = Booking.query.get_or_404(booking_id)
        
        if booking.status != 'checked_in':
            return jsonify({'error': 'Only checked-in bookings can be checked out'}), 400
        
        # Use booking service to check-out
        booking_service = BookingService()
        booking_service.checkout_booking(booking_id)
        
        return jsonify({
            'message': 'Check-out successful',
            'booking': booking.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Check-out error: {str(e)}")
        return jsonify({'error': 'Check-out failed'}), 500

def _create_or_find_guest(guest_info):
    """Create or find guest based on information"""
    # Try to find existing guest by email
    if guest_info.get('email'):
        guest = Guest.query.filter_by(email=guest_info['email']).first()
        if guest:
            return guest
    
    # Create new guest
    guest = Guest(
        first_name=guest_info['first_name'],
        last_name=guest_info['last_name'],
        email=guest_info.get('email'),
        phone=guest_info.get('phone'),
        nationality=guest_info.get('nationality'),
        date_of_birth=guest_info.get('date_of_birth')
    )
    
    db.session.add(guest)
    db.session.commit()
    
    return guest

def _is_admin(user_id):
    """Check if user is admin"""
    user = User.query.get(user_id)
    return user and user.is_admin()
