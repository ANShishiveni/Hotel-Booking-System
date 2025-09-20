"""
Hotel routes for managing hotels and room types
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, limiter
from app.models.user import User
from app.models.hotel import Hotel, RoomType, Room
from app.utils.decorators import validate_json, require_permissions
from app.utils.validators import validate_email
from datetime import datetime
import json

hotels_bp = Blueprint('hotels', __name__)

@hotels_bp.route('/', methods=['GET'])
@limiter.limit("60 per minute")
def get_hotels():
    """Get list of hotels"""
    try:
        # Get query parameters
        city = request.args.get('city')
        country = request.args.get('country')
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = Hotel.query.filter_by(is_active=True)
        
        if city:
            query = query.filter(Hotel.city.ilike(f'%{city}%'))
        
        if country:
            query = query.filter(Hotel.country.ilike(f'%{country}%'))
        
        # Apply pagination
        hotels = query.offset(offset).limit(limit).all()
        total = query.count()
        
        return jsonify({
            'hotels': [hotel.to_dict() for hotel in hotels],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get hotels error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve hotels'}), 500

@hotels_bp.route('/<int:hotel_id>', methods=['GET'])
@limiter.limit("60 per minute")
def get_hotel(hotel_id):
    """Get specific hotel details"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        
        if not hotel.is_active:
            return jsonify({'error': 'Hotel not found'}), 404
        
        # Get room types for this hotel
        room_types = RoomType.query.filter_by(
            hotel_id=hotel_id,
            is_active=True
        ).all()
        
        hotel_data = hotel.to_dict()
        hotel_data['room_types'] = [rt.to_dict() for rt in room_types]
        
        return jsonify({'hotel': hotel_data}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get hotel error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve hotel'}), 500

@hotels_bp.route('/<int:hotel_id>/room-types', methods=['GET'])
@limiter.limit("60 per minute")
def get_hotel_room_types(hotel_id):
    """Get room types for a specific hotel"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        
        if not hotel.is_active:
            return jsonify({'error': 'Hotel not found'}), 404
        
        room_types = RoomType.query.filter_by(
            hotel_id=hotel_id,
            is_active=True
        ).all()
        
        return jsonify({
            'hotel_id': hotel_id,
            'hotel_name': hotel.name,
            'room_types': [rt.to_dict() for rt in room_types]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get room types error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve room types'}), 500

@hotels_bp.route('/', methods=['POST'])
@jwt_required()
@require_permissions(['admin_all'])
@validate_json(['name', 'address', 'city', 'country'])
def create_hotel():
    """Create a new hotel (admin only)"""
    try:
        data = request.get_json()
        
        # Validate email if provided
        if data.get('email') and not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Create hotel
        hotel = Hotel(
            name=data['name'],
            address=data['address'],
            city=data['city'],
            state=data.get('state'),
            country=data['country'],
            postal_code=data.get('postal_code'),
            phone=data.get('phone'),
            email=data.get('email'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            amenities=data.get('amenities', [])
        )
        
        db.session.add(hotel)
        db.session.commit()
        
        return jsonify({
            'message': 'Hotel created successfully',
            'hotel': hotel.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create hotel error: {str(e)}")
        return jsonify({'error': 'Hotel creation failed'}), 500

@hotels_bp.route('/<int:hotel_id>', methods=['PUT'])
@jwt_required()
@require_permissions(['admin_all'])
@validate_json(['name', 'address', 'city', 'country'])
def update_hotel(hotel_id):
    """Update hotel information (admin only)"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        data = request.get_json()
        
        # Validate email if provided
        if data.get('email') and not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Update hotel fields
        hotel.name = data['name']
        hotel.address = data['address']
        hotel.city = data['city']
        hotel.state = data.get('state')
        hotel.country = data['country']
        hotel.postal_code = data.get('postal_code')
        hotel.phone = data.get('phone')
        hotel.email = data.get('email')
        hotel.latitude = data.get('latitude')
        hotel.longitude = data.get('longitude')
        hotel.amenities = data.get('amenities', [])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Hotel updated successfully',
            'hotel': hotel.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update hotel error: {str(e)}")
        return jsonify({'error': 'Hotel update failed'}), 500

@hotels_bp.route('/<int:hotel_id>/room-types', methods=['POST'])
@jwt_required()
@require_permissions(['admin_all'])
@validate_json(['name', 'description', 'max_occupancy', 'base_price'])
def create_room_type(hotel_id):
    """Create a new room type for a hotel (admin only)"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        data = request.get_json()
        
        # Validate occupancy
        if data['max_occupancy'] <= 0:
            return jsonify({'error': 'Max occupancy must be positive'}), 400
        
        # Validate base price
        if data['base_price'] < 0:
            return jsonify({'error': 'Base price must be non-negative'}), 400
        
        # Create room type
        room_type = RoomType(
            hotel_id=hotel_id,
            name=data['name'],
            description=data['description'],
            max_occupancy=data['max_occupancy'],
            amenities=data.get('amenities', []),
            base_price=data['base_price'],
            pricing_rules=data.get('pricing_rules', {})
        )
        
        db.session.add(room_type)
        db.session.commit()
        
        return jsonify({
            'message': 'Room type created successfully',
            'room_type': room_type.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create room type error: {str(e)}")
        return jsonify({'error': 'Room type creation failed'}), 500

@hotels_bp.route('/room-types/<int:room_type_id>', methods=['PUT'])
@jwt_required()
@require_permissions(['admin_all'])
@validate_json(['name', 'description', 'max_occupancy', 'base_price'])
def update_room_type(room_type_id):
    """Update room type information (admin only)"""
    try:
        room_type = RoomType.query.get_or_404(room_type_id)
        data = request.get_json()
        
        # Validate occupancy
        if data['max_occupancy'] <= 0:
            return jsonify({'error': 'Max occupancy must be positive'}), 400
        
        # Validate base price
        if data['base_price'] < 0:
            return jsonify({'error': 'Base price must be non-negative'}), 400
        
        # Update room type fields
        room_type.name = data['name']
        room_type.description = data['description']
        room_type.max_occupancy = data['max_occupancy']
        room_type.amenities = data.get('amenities', [])
        room_type.base_price = data['base_price']
        room_type.pricing_rules = data.get('pricing_rules', {})
        
        db.session.commit()
        
        return jsonify({
            'message': 'Room type updated successfully',
            'room_type': room_type.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update room type error: {str(e)}")
        return jsonify({'error': 'Room type update failed'}), 500

@hotels_bp.route('/<int:hotel_id>/rooms', methods=['POST'])
@jwt_required()
@require_permissions(['admin_all'])
@validate_json(['room_type_id', 'room_number'])
def create_room(hotel_id):
    """Create a new room for a hotel (admin only)"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        data = request.get_json()
        
        # Check if room type belongs to this hotel
        room_type = RoomType.query.filter_by(
            id=data['room_type_id'],
            hotel_id=hotel_id
        ).first_or_404()
        
        # Check if room number already exists for this hotel
        existing_room = Room.query.filter_by(
            hotel_id=hotel_id,
            room_number=data['room_number']
        ).first()
        
        if existing_room:
            return jsonify({'error': 'Room number already exists for this hotel'}), 409
        
        # Create room
        room = Room(
            hotel_id=hotel_id,
            room_type_id=data['room_type_id'],
            room_number=data['room_number'],
            floor=data.get('floor'),
            features=data.get('features', {})
        )
        
        db.session.add(room)
        db.session.commit()
        
        return jsonify({
            'message': 'Room created successfully',
            'room': room.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create room error: {str(e)}")
        return jsonify({'error': 'Room creation failed'}), 500
