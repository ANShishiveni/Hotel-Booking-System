from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Hotel, Room, RoomType, Booking, Guest, AuditLog
from app import db
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, func, select, update
from sqlalchemy.exc import IntegrityError
import uuid

bookings_bp = Blueprint('bookings', __name__)

@bookings_bp.route('/', methods=['GET'])
@jwt_required()
def get_user_bookings():
    """Get all bookings for the current user"""
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        
        query = Booking.query.filter_by(user_id=current_user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        bookings = query.order_by(Booking.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'bookings': [booking.to_dict() for booking in bookings.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': bookings.total,
                'pages': bookings.pages,
                'has_next': bookings.has_next,
                'has_prev': bookings.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting user bookings: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bookings_bp.route('/<int:booking_id>', methods=['GET'])
@jwt_required()
def get_booking(booking_id):
    """Get specific booking details"""
    try:
        current_user_id = get_jwt_identity()
        booking = Booking.query.filter_by(id=booking_id, user_id=current_user_id).first()
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        return jsonify({'booking': booking.to_dict()})
        
    except Exception as e:
        current_app.logger.error(f"Error getting booking: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bookings_bp.route('/', methods=['POST'])
@jwt_required()
def create_booking():
    """Create a new booking with concurrency control"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['hotel_id', 'room_type_id', 'check_in_date', 'check_out_date', 'guests']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Parse dates
        check_in_date = datetime.strptime(data['check_in_date'], '%Y-%m-%d').date()
        check_out_date = datetime.strptime(data['check_out_date'], '%Y-%m-%d').date()
        
        # Validate dates
        if check_out_date <= check_in_date:
            return jsonify({'error': 'Check-out date must be after check-in date'}), 400
        
        if check_in_date < date.today():
            return jsonify({'error': 'Check-in date cannot be in the past'}), 400
        
        # Validate guests data
        guests_data = data['guests']
        if not isinstance(guests_data, list) or len(guests_data) == 0:
            return jsonify({'error': 'At least one guest is required'}), 400
        
        # Get hotel and room type
        hotel = Hotel.query.get(data['hotel_id'])
        if not hotel or not hotel.is_active:
            return jsonify({'error': 'Hotel not found or inactive'}), 404
        
        room_type = RoomType.query.filter_by(
            id=data['room_type_id'], 
            hotel_id=data['hotel_id'], 
            is_active=True
        ).first()
        
        if not room_type:
            return jsonify({'error': 'Room type not found or inactive'}), 404
        
        # Calculate total guests
        total_adults = sum(guest.get('adults', 1) for guest in guests_data)
        total_children = sum(guest.get('children', 0) for guest in guests_data)
        
        if total_adults > room_type.max_occupancy:
            return jsonify({'error': f'Room type can only accommodate {room_type.max_occupancy} guests'}), 400
        
        # Start database transaction with concurrency control
        try:
            # Use SELECT FOR UPDATE to lock available rooms
            available_room = db.session.query(Room)\
                .outerjoin(Booking, and_(
                    Booking.room_id == Room.id,
                    or_(
                        and_(Booking.check_in_date <= check_in_date, Booking.check_out_date > check_in_date),
                        and_(Booking.check_in_date < check_out_date, Booking.check_out_date >= check_out_date),
                        and_(Booking.check_in_date >= check_in_date, Booking.check_out_date <= check_out_date)
                    ),
                    Booking.status.in_(['confirmed', 'checked_in'])
                ))\
                .filter(
                    Room.room_type_id == room_type.id,
                    Room.is_active == True,
                    Booking.id.is_(None)
                )\
                .with_for_update()\
                .first()
            
            if not available_room:
                return jsonify({'error': 'No rooms available for the selected dates'}), 409
            
            # Calculate pricing
            nights = (check_out_date - check_in_date).days
            room_rate = float(room_type.base_price)
            subtotal = room_rate * nights
            
            # Apply any discounts (mock calculation)
            discount_amount = 0
            if nights >= 7:  # Weekly discount
                discount_amount = subtotal * 0.1
            
            # Calculate tax (15% VAT for Namibia)
            tax_rate = 0.15
            tax_amount = (subtotal - discount_amount) * tax_rate
            total_amount = subtotal - discount_amount + tax_amount
            
            # Create booking
            booking = Booking(
                booking_reference=Booking().generate_booking_reference(),
                user_id=current_user_id,
                hotel_id=hotel.id,
                room_id=available_room.id,
                room_type_id=room_type.id,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                nights=nights,
                adults=total_adults,
                children=total_children,
                room_rate=room_rate,
                total_amount=total_amount,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                status='pending',
                special_requests=data.get('special_requests', ''),
                guest_notes=data.get('guest_notes', '')
            )
            
            db.session.add(booking)
            db.session.flush()  # Get booking ID
            
            # Create guest records
            for i, guest_data in enumerate(guests_data):
                guest = Guest(
                    booking_id=booking.id,
                    first_name=guest_data['first_name'],
                    last_name=guest_data['last_name'],
                    email=guest_data.get('email', ''),
                    phone=guest_data.get('phone', ''),
                    date_of_birth=datetime.strptime(guest_data['date_of_birth'], '%Y-%m-%d').date() if guest_data.get('date_of_birth') else None,
                    nationality=guest_data.get('nationality', ''),
                    id_number=guest_data.get('id_number', ''),
                    passport_number=guest_data.get('passport_number', ''),
                    is_primary_guest=(i == 0)
                )
                db.session.add(guest)
            
            # Create audit log
            audit_log = AuditLog(
                table_name='bookings',
                record_id=booking.id,
                action='CREATE',
                new_values=booking.to_dict(),
                user_id=current_user_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
            
            # Commit transaction
            db.session.commit()
            
            return jsonify({
                'message': 'Booking created successfully',
                'booking': booking.to_dict()
            }), 201
            
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Integrity error in booking creation: {str(e)}")
            return jsonify({'error': 'Booking creation failed due to concurrency conflict'}), 409
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': 'Invalid date format'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating booking: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bookings_bp.route('/<int:booking_id>/confirm', methods=['POST'])
@jwt_required()
def confirm_booking(booking_id):
    """Confirm a pending booking"""
    try:
        current_user_id = get_jwt_identity()
        
        # Start transaction
        with db.session.begin():
            # Lock booking for update
            booking = db.session.query(Booking)\
                .filter_by(id=booking_id, user_id=current_user_id)\
                .with_for_update()\
                .first()
            
            if not booking:
                return jsonify({'error': 'Booking not found'}), 404
            
            if booking.status != 'pending':
                return jsonify({'error': f'Booking cannot be confirmed. Current status: {booking.status}'}), 400
            
            # Update booking status
            booking.status = 'confirmed'
            booking.confirmed_at = datetime.utcnow()
            
            # Create audit log
            audit_log = AuditLog(
                table_name='bookings',
                record_id=booking.id,
                action='UPDATE',
                old_values={'status': 'pending'},
                new_values={'status': 'confirmed', 'confirmed_at': booking.confirmed_at.isoformat()},
                user_id=current_user_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
        
        return jsonify({
            'message': 'Booking confirmed successfully',
            'booking': booking.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error confirming booking: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bookings_bp.route('/<int:booking_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_booking(booking_id):
    """Cancel a booking"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}
        cancellation_reason = data.get('reason', '')
        
        # Start transaction
        with db.session.begin():
            # Lock booking for update
            booking = db.session.query(Booking)\
                .filter_by(id=booking_id, user_id=current_user_id)\
                .with_for_update()\
                .first()
            
            if not booking:
                return jsonify({'error': 'Booking not found'}), 404
            
            if booking.status in ['cancelled', 'checked_out']:
                return jsonify({'error': f'Booking cannot be cancelled. Current status: {booking.status}'}), 400
            
            # Check cancellation policy
            days_until_checkin = (booking.check_in_date - date.today()).days
            cancellation_fee = 0
            
            if days_until_checkin < 1:
                cancellation_fee = booking.total_amount  # No refund for same-day cancellation
            elif days_until_checkin < 3:
                cancellation_fee = booking.total_amount * 0.5  # 50% fee for 1-2 days
            elif days_until_checkin < 7:
                cancellation_fee = booking.total_amount * 0.25  # 25% fee for 3-6 days
            
            # Update booking status
            booking.status = 'cancelled'
            booking.cancelled_at = datetime.utcnow()
            if cancellation_reason:
                booking.guest_notes = f"{booking.guest_notes or ''}\nCancellation reason: {cancellation_reason}"
            
            # Create audit log
            audit_log = AuditLog(
                table_name='bookings',
                record_id=booking.id,
                action='UPDATE',
                old_values={'status': booking.status, 'cancelled_at': None},
                new_values={
                    'status': 'cancelled', 
                    'cancelled_at': booking.cancelled_at.isoformat(),
                    'cancellation_fee': cancellation_fee
                },
                user_id=current_user_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
        
        refund_amount = booking.total_amount - cancellation_fee
        
        return jsonify({
            'message': 'Booking cancelled successfully',
            'booking': booking.to_dict(),
            'cancellation_details': {
                'cancellation_fee': cancellation_fee,
                'refund_amount': refund_amount,
                'days_until_checkin': days_until_checkin
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error cancelling booking: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bookings_bp.route('/<int:booking_id>/modify', methods=['PUT'])
@jwt_required()
def modify_booking(booking_id):
    """Modify a booking (limited changes allowed)"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Start transaction
        with db.session.begin():
            # Lock booking for update
            booking = db.session.query(Booking)\
                .filter_by(id=booking_id, user_id=current_user_id)\
                .with_for_update()\
                .first()
            
            if not booking:
                return jsonify({'error': 'Booking not found'}), 404
            
            if booking.status not in ['pending', 'confirmed']:
                return jsonify({'error': f'Booking cannot be modified. Current status: {booking.status}'}), 400
            
            # Store old values
            old_values = booking.to_dict()
            
            # Allow modification of certain fields only
            modified = False
            
            if 'special_requests' in data:
                booking.special_requests = data['special_requests']
                modified = True
            
            if 'guest_notes' in data:
                booking.guest_notes = data['guest_notes']
                modified = True
            
            if not modified:
                return jsonify({'error': 'No valid fields to modify'}), 400
            
            # Create audit log
            audit_log = AuditLog(
                table_name='bookings',
                record_id=booking.id,
                action='UPDATE',
                old_values=old_values,
                new_values=booking.to_dict(),
                user_id=current_user_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
        
        return jsonify({
            'message': 'Booking modified successfully',
            'booking': booking.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error modifying booking: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bookings_bp.route('/<int:booking_id>/check-in', methods=['POST'])
@jwt_required()
def check_in_booking(booking_id):
    """Check in a booking (hotel staff only)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user has staff role
        if not user or not user.has_role('staff'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # Start transaction
        with db.session.begin():
            # Lock booking for update
            booking = db.session.query(Booking)\
                .filter_by(id=booking_id)\
                .with_for_update()\
                .first()
            
            if not booking:
                return jsonify({'error': 'Booking not found'}), 404
            
            if booking.status != 'confirmed':
                return jsonify({'error': f'Booking cannot be checked in. Current status: {booking.status}'}), 400
            
            # Check if check-in date is today or past
            if booking.check_in_date > date.today():
                return jsonify({'error': 'Cannot check in before check-in date'}), 400
            
            # Update booking status
            booking.status = 'checked_in'
            
            # Create audit log
            audit_log = AuditLog(
                table_name='bookings',
                record_id=booking.id,
                action='UPDATE',
                old_values={'status': 'confirmed'},
                new_values={'status': 'checked_in'},
                user_id=current_user_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
        
        return jsonify({
            'message': 'Booking checked in successfully',
            'booking': booking.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error checking in booking: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bookings_bp.route('/<int:booking_id>/check-out', methods=['POST'])
@jwt_required()
def check_out_booking(booking_id):
    """Check out a booking (hotel staff only)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user has staff role
        if not user or not user.has_role('staff'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # Start transaction
        with db.session.begin():
            # Lock booking for update
            booking = db.session.query(Booking)\
                .filter_by(id=booking_id)\
                .with_for_update()\
                .first()
            
            if not booking:
                return jsonify({'error': 'Booking not found'}), 404
            
            if booking.status != 'checked_in':
                return jsonify({'error': f'Booking cannot be checked out. Current status: {booking.status}'}), 400
            
            # Update booking status
            booking.status = 'checked_out'
            
            # Create audit log
            audit_log = AuditLog(
                table_name='bookings',
                record_id=booking.id,
                action='UPDATE',
                old_values={'status': 'checked_in'},
                new_values={'status': 'checked_out'},
                user_id=current_user_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
        
        return jsonify({
            'message': 'Booking checked out successfully',
            'booking': booking.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error checking out booking: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bookings_bp.route('/availability', methods=['POST'])
def check_availability():
    """Check room availability for specific dates and room type"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['hotel_id', 'room_type_id', 'check_in_date', 'check_out_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Parse dates
        check_in_date = datetime.strptime(data['check_in_date'], '%Y-%m-%d').date()
        check_out_date = datetime.strptime(data['check_out_date'], '%Y-%m-%d').date()
        
        # Validate dates
        if check_out_date <= check_in_date:
            return jsonify({'error': 'Check-out date must be after check-in date'}), 400
        
        # Get room type
        room_type = RoomType.query.filter_by(
            id=data['room_type_id'],
            hotel_id=data['hotel_id'],
            is_active=True
        ).first()
        
        if not room_type:
            return jsonify({'error': 'Room type not found'}), 404
        
        # Check availability with FOR UPDATE to prevent race conditions
        available_rooms = db.session.query(Room)\
            .outerjoin(Booking, and_(
                Booking.room_id == Room.id,
                or_(
                    and_(Booking.check_in_date <= check_in_date, Booking.check_out_date > check_in_date),
                    and_(Booking.check_in_date < check_out_date, Booking.check_out_date >= check_out_date),
                    and_(Booking.check_in_date >= check_in_date, Booking.check_out_date <= check_out_date)
                ),
                Booking.status.in_(['confirmed', 'checked_in'])
            ))\
            .filter(
                Room.room_type_id == room_type.id,
                Room.is_active == True,
                Booking.id.is_(None)
            )\
            .with_for_update(skip_locked=True)\
            .all()
        
        return jsonify({
            'available': len(available_rooms) > 0,
            'available_rooms': len(available_rooms),
            'room_type': room_type.to_dict(),
            'search_params': {
                'check_in_date': check_in_date.isoformat(),
                'check_out_date': check_out_date.isoformat(),
                'hotel_id': data['hotel_id'],
                'room_type_id': data['room_type_id']
            }
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    except Exception as e:
        current_app.logger.error(f"Error checking availability: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
