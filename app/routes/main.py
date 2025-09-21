from flask import Blueprint, render_template, request, jsonify, current_app
from app.models import Hotel, RoomType, Room, Booking, Review
from app import db
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, date, timedelta
import pytz

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page with featured hotels"""
    try:
        # Get featured hotels (highest rated, active)
        try:
            # Get hotels with reviews first
            featured_hotels = db.session.query(Hotel)\
                .filter(Hotel.is_active == True)\
                .outerjoin(Review, and_(Review.hotel_id == Hotel.id, Review.is_active == True))\
                .group_by(Hotel.id)\
                .having(func.avg(Review.rating).isnot(None))\
                .order_by(desc(func.avg(Review.rating)))\
                .limit(6).all()
            
            # If no hotels with reviews, get any active hotels
            if not featured_hotels:
                featured_hotels = Hotel.query.filter_by(is_active=True).limit(6).all()
                
        except Exception as e:
            current_app.logger.error(f"Error loading featured hotels: {str(e)}")
            # Fallback to simple query
            featured_hotels = Hotel.query.filter_by(is_active=True).limit(6).all()
        
        return render_template('index.html', hotels=featured_hotels)
    except Exception as e:
        current_app.logger.error(f"Error loading home page: {str(e)}")
        return render_template('index.html', hotels=[])

@main_bp.route('/search')
def search_hotels():
    """Search hotels page"""
    return render_template('search.html')

@main_bp.route('/hotels')
def hotels():
    """List all hotels"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 12
        
        # Filters
        city = request.args.get('city', '')
        star_rating = request.args.get('star_rating', type=int)
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        
        # Build query
        query = Hotel.query.filter_by(is_active=True)
        
        if city:
            query = query.filter(Hotel.city.ilike(f'%{city}%'))
        
        if star_rating:
            query = query.filter(Hotel.star_rating >= star_rating)
        
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
        
        return render_template('hotels.html', hotels=hotels)
    except Exception as e:
        current_app.logger.error(f"Error loading hotels: {str(e)}")
        return render_template('hotels.html', hotels=None)

@main_bp.route('/hotel/<int:hotel_id>')
def hotel_detail(hotel_id):
    """Hotel detail page"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        
        # Get room types for this hotel
        room_types = RoomType.query.filter_by(hotel_id=hotel_id, is_active=True).all()
        
        # Get recent reviews
        reviews = Review.query.filter_by(hotel_id=hotel_id, is_active=True)\
            .order_by(desc(Review.created_at)).limit(10).all()
        
        # Calculate average rating
        avg_rating = db.session.query(func.avg(Review.rating))\
            .filter_by(hotel_id=hotel_id, is_active=True).scalar()
        
        return render_template('hotel_detail.html', 
                             hotel=hotel, 
                             room_types=room_types,
                             reviews=reviews,
                             avg_rating=avg_rating)
    except Exception as e:
        current_app.logger.error(f"Error loading hotel detail: {str(e)}")
        return render_template('error.html', error="Hotel not found"), 404

@main_bp.route('/api/search', methods=['POST'])
def api_search():
    """Optimized API endpoint for hotel search with availability"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not all(k in data for k in ['check_in', 'check_out', 'guests']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        check_in = data['check_in']
        check_out = data['check_out']
        guests = data['guests']
        city = data.get('city', '')
        
        # Validate dates
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        
        if check_out_date <= check_in_date:
            return jsonify({'error': 'Check-out date must be after check-in date'}), 400
        
        if check_in_date < date.today():
            return jsonify({'error': 'Check-in date cannot be in the past'}), 400
        
        # Simplified but optimized search
        # Get hotels with available rooms using a single query with joins
        available_hotels = []
        
        # Get all hotels that match the criteria
        hotels = Hotel.query.filter_by(is_active=True)
        if city:
            hotels = hotels.filter(Hotel.city.ilike(f'%{city}%'))
        
        for hotel in hotels:
            # Get room types for this hotel
            room_types = RoomType.query.filter_by(
                hotel_id=hotel.id,
                is_active=True
            ).filter(RoomType.max_occupancy >= guests).all()
            
            hotel_room_types = []
            min_price = float('inf')
            
            for room_type in room_types:
                # Count available rooms for this room type
                available_rooms = db.session.query(Room)\
                    .outerjoin(Booking, and_(
                        Booking.room_id == Room.id,
                        Booking.status.in_(['confirmed', 'checked_in']),
                        or_(
                            and_(Booking.check_in_date <= check_in_date, Booking.check_out_date > check_in_date),
                            and_(Booking.check_in_date < check_out_date, Booking.check_out_date >= check_out_date),
                            and_(Booking.check_in_date >= check_in_date, Booking.check_out_date <= check_out_date)
                        )
                    ))\
                    .filter(
                        Room.room_type_id == room_type.id,
                        Room.is_active == True,
                        Booking.id.is_(None)
                    ).count()
                
                if available_rooms > 0:
                    room_type_dict = room_type.to_dict()
                    room_type_dict['available_rooms'] = available_rooms
                    hotel_room_types.append(room_type_dict)
                    min_price = min(min_price, float(room_type.base_price))
            
            if hotel_room_types:
                hotel_dict = hotel.to_dict()
                hotel_dict['available_room_types'] = hotel_room_types
                hotel_dict['min_price'] = min_price
                available_hotels.append(hotel_dict)
        
        # Sort by minimum price
        available_hotels.sort(key=lambda x: x['min_price'])
        
        return jsonify({
            'hotels': available_hotels,
            'search_params': {
                'check_in': check_in_date.isoformat(),
                'check_out': check_out_date.isoformat(),
                'guests': guests,
                'city': city
            }
        })
        
    except ValueError as e:
        return jsonify({'error': 'Invalid date format'}), 400
    except Exception as e:
        current_app.logger.error(f"Error in hotel search: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@main_bp.route('/api/hotels/<int:hotel_id>/availability')
def api_hotel_availability(hotel_id):
    """Get room availability for a specific hotel"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        
        check_in = request.args.get('check_in')
        check_out = request.args.get('check_out')
        guests = request.args.get('guests', 1, type=int)
        
        if not check_in or not check_out:
            return jsonify({'error': 'check_in and check_out dates are required'}), 400
        
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        
        # Get room types with availability
        room_types = RoomType.query.filter_by(hotel_id=hotel_id, is_active=True).all()
        availability = []
        
        for room_type in room_types:
            if room_type.max_occupancy < guests:
                continue
                
            # Count available rooms
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
        current_app.logger.error(f"Error checking availability: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@main_bp.route('/api/contact', methods=['POST'])
def contact_submit():
    """Handle contact form submission"""
    try:
        data = request.get_json() or request.form.to_dict()
        
        # Validate required fields
        required_fields = ['firstName', 'lastName', 'email', 'subject', 'message']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        # Here you would typically:
        # 1. Send an email to the admin
        # 2. Store the message in the database
        # 3. Send a confirmation email to the user
        
        # For now, just log the message
        current_app.logger.info(f"Contact form submission from {data['email']}: {data['subject']}")
        
        return jsonify({
            'success': True,
            'message': 'Thank you for your message! We will get back to you soon.'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error processing contact form: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while processing your message. Please try again.'
        }), 500

@main_bp.route('/booking')
def booking_page():
    """Booking page for making reservations"""
    try:
        # Get booking parameters from query string
        check_in = request.args.get('check_in')
        check_out = request.args.get('check_out')
        guests = request.args.get('guests', type=int)
        hotel_id = request.args.get('hotel_id', type=int)
        room_type_id = request.args.get('room_type_id', type=int)
        
        # Validate required parameters
        if not all([check_in, check_out, guests, hotel_id]):
            return render_template('error.html', error="Missing booking parameters")
        
        # Get hotel and room type information
        hotel = Hotel.query.get_or_404(hotel_id)
        room_type = None
        
        if room_type_id:
            room_type = RoomType.query.get_or_404(room_type_id)
        
        return render_template('booking.html', 
                             hotel=hotel,
                             room_type=room_type,
                             check_in=check_in,
                             check_out=check_out,
                             guests=guests)
    except Exception as e:
        current_app.logger.error(f"Error loading booking page: {str(e)}")
        return render_template('error.html', error="Booking page not available")

@main_bp.route('/profile')
def profile_page():
    """User profile page"""
    return render_template('profile.html')

@main_bp.route('/my-bookings')
def my_bookings_page():
    """User's bookings page"""
    return render_template('my_bookings.html')

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/api/stats')
def api_stats():
    """Get system statistics"""
    try:
        stats = {
            'hotels': Hotel.query.filter_by(is_active=True).count(),
            'rooms': Room.query.filter_by(is_active=True).count(),
            'bookings': Booking.query.count(),
            'reviews': Review.query.filter_by(is_active=True).count()
        }
        return jsonify(stats)
    except Exception as e:
        current_app.logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
