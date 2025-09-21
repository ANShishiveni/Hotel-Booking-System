from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Hotel, RoomType, Room, Review
from app import db
from sqlalchemy import and_, or_, func, desc
import os

hotels_bp = Blueprint('hotels', __name__)

@hotels_bp.route('/', methods=['GET'])
def get_hotels():
    """Get all hotels with filtering and pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        
        # Filters
        city = request.args.get('city', '')
        star_rating = request.args.get('star_rating', type=int)
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        search = request.args.get('search', '')
        
        # Build query
        query = Hotel.query.filter_by(is_active=True)
        
        if city:
            query = query.filter(Hotel.city.ilike(f'%{city}%'))
        
        if star_rating:
            query = query.filter(Hotel.star_rating >= star_rating)
        
        if search:
            query = query.filter(
                or_(
                    Hotel.name.ilike(f'%{search}%'),
                    Hotel.description.ilike(f'%{search}%'),
                    Hotel.city.ilike(f'%{search}%')
                )
            )
        
        # Apply price filters by joining with room types
        if min_price or max_price:
            query = query.join(RoomType)
            if min_price:
                query = query.filter(RoomType.base_price >= min_price)
            if max_price:
                query = query.filter(RoomType.base_price <= max_price)
        
        hotels = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'hotels': [hotel.to_dict() for hotel in hotels.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': hotels.total,
                'pages': hotels.pages,
                'has_next': hotels.has_next,
                'has_prev': hotels.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting hotels: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@hotels_bp.route('/<int:hotel_id>', methods=['GET'])
def get_hotel(hotel_id):
    """Get specific hotel details"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        
        if not hotel.is_active:
            return jsonify({'error': 'Hotel is not active'}), 404
        
        return jsonify({'hotel': hotel.to_dict()})
        
    except Exception as e:
        current_app.logger.error(f"Error getting hotel: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@hotels_bp.route('/<int:hotel_id>/room-types', methods=['GET'])
def get_hotel_room_types(hotel_id):
    """Get room types for a specific hotel"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        
        if not hotel.is_active:
            return jsonify({'error': 'Hotel is not active'}), 404
        
        room_types = RoomType.query.filter_by(hotel_id=hotel_id, is_active=True).all()
        
        return jsonify({
            'hotel': hotel.to_dict(),
            'room_types': [rt.to_dict() for rt in room_types]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting room types: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@hotels_bp.route('/<int:hotel_id>/reviews', methods=['GET'])
def get_hotel_reviews(hotel_id):
    """Get reviews for a specific hotel"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        
        if not hotel.is_active:
            return jsonify({'error': 'Hotel is not active'}), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        reviews = Review.query.filter_by(hotel_id=hotel_id, is_active=True)\
            .order_by(desc(Review.created_at))\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        # Calculate average rating
        avg_rating = db.session.query(func.avg(Review.rating))\
            .filter_by(hotel_id=hotel_id, is_active=True).scalar()
        
        # Rating distribution
        rating_distribution = db.session.query(
            Review.rating, func.count(Review.id)
        ).filter_by(hotel_id=hotel_id, is_active=True)\
         .group_by(Review.rating)\
         .all()
        
        return jsonify({
            'hotel': hotel.to_dict(),
            'reviews': [review.to_dict() for review in reviews.items],
            'average_rating': float(avg_rating) if avg_rating else 0,
            'total_reviews': reviews.total,
            'rating_distribution': dict(rating_distribution),
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': reviews.total,
                'pages': reviews.pages,
                'has_next': reviews.has_next,
                'has_prev': reviews.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting hotel reviews: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@hotels_bp.route('/<int:hotel_id>/availability', methods=['POST'])
def check_hotel_availability(hotel_id):
    """Check room availability for a hotel"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        
        if not hotel.is_active:
            return jsonify({'error': 'Hotel is not active'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        if not data or not all(k in data for k in ['check_in', 'check_out']):
            return jsonify({'error': 'check_in and check_out dates are required'}), 400
        
        from datetime import datetime, date
        
        check_in_date = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
        check_out_date = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
        guests = data.get('guests', 1)
        
        # Validate dates
        if check_out_date <= check_in_date:
            return jsonify({'error': 'Check-out date must be after check-in date'}), 400
        
        if check_in_date < date.today():
            return jsonify({'error': 'Check-in date cannot be in the past'}), 400
        
        # Get room types with availability
        room_types = RoomType.query.filter_by(hotel_id=hotel_id, is_active=True).all()
        availability = []
        
        for room_type in room_types:
            if room_type.max_occupancy < guests:
                continue
            
            # Count available rooms
            available_rooms = db.session.query(Room)\
                .outerjoin(db.session.query(Booking)\
                    .filter(
                        or_(
                            and_(Booking.check_in_date <= check_in_date, Booking.check_out_date > check_in_date),
                            and_(Booking.check_in_date < check_out_date, Booking.check_out_date >= check_out_date),
                            and_(Booking.check_in_date >= check_in_date, Booking.check_out_date <= check_out_date)
                        ),
                        Booking.status.in_(['confirmed', 'checked_in'])
                    ), Booking.room_id == Room.id, isouter=True)\
                .filter(
                    Room.room_type_id == room_type.id,
                    Room.is_active == True,
                    Booking.id.is_(None)
                ).count()
            
            if available_rooms > 0:
                room_type_dict = room_type.to_dict()
                room_type_dict['available_rooms'] = available_rooms
                availability.append(room_type_dict)
        
        return jsonify({
            'hotel': hotel.to_dict(),
            'availability': availability,
            'search_params': {
                'check_in': check_in_date.isoformat(),
                'check_out': check_out_date.isoformat(),
                'guests': guests
            }
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    except Exception as e:
        current_app.logger.error(f"Error checking hotel availability: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@hotels_bp.route('/', methods=['POST'])
@jwt_required()
def create_hotel():
    """Create a new hotel (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user has admin role
        if not user or not user.has_role('admin'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'address', 'city', 'country']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create hotel
        hotel = Hotel(
            name=data['name'],
            description=data.get('description', ''),
            address=data['address'],
            city=data['city'],
            state=data.get('state', ''),
            country=data['country'],
            postal_code=data.get('postal_code', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            website=data.get('website', ''),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            star_rating=data.get('star_rating', 3),
            amenities=data.get('amenities', []),
            images=data.get('images', []),
            policies=data.get('policies', {})
        )
        
        db.session.add(hotel)
        db.session.commit()
        
        return jsonify({
            'message': 'Hotel created successfully',
            'hotel': hotel.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating hotel: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@hotels_bp.route('/<int:hotel_id>', methods=['PUT'])
@jwt_required()
def update_hotel(hotel_id):
    """Update hotel information (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user has admin role
        if not user or not user.has_role('admin'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        hotel = Hotel.query.get_or_404(hotel_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update allowed fields
        allowed_fields = [
            'name', 'description', 'address', 'city', 'state', 'country',
            'postal_code', 'phone', 'email', 'website', 'latitude', 'longitude',
            'star_rating', 'amenities', 'images', 'policies', 'is_active'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(hotel, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Hotel updated successfully',
            'hotel': hotel.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating hotel: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@hotels_bp.route('/<int:hotel_id>', methods=['DELETE'])
@jwt_required()
def delete_hotel(hotel_id):
    """Delete a hotel (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user has admin role
        if not user or not user.has_role('admin'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        hotel = Hotel.query.get_or_404(hotel_id)
        
        # Soft delete by setting is_active to False
        hotel.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'Hotel deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting hotel: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
