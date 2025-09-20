"""
Test configuration and fixtures for the Hotel Booking System
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta
from decimal import Decimal

from app import create_app, db
from app.models.user import User, Role
from app.models.hotel import Hotel, RoomType, Room
from app.models.booking import Booking, BookingRoom, Guest
from app.models.payment import Payment
from app.models.review import Review
from app.models.audit import AuditLog

@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'JWT_SECRET_KEY': 'test-jwt-secret',
        'SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        
        # Create test roles
        admin_role = Role(
            name='admin',
            description='Administrator role',
            permissions=['admin_all', 'manage_users', 'manage_hotels']
        )
        customer_role = Role(
            name='customer',
            description='Customer role',
            permissions=['book_room', 'view_bookings', 'write_reviews']
        )
        db.session.add_all([admin_role, customer_role])
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()

@pytest.fixture
def db_session(app):
    """Create database session for testing"""
    with app.app_context():
        yield db.session

@pytest.fixture
def admin_role(db_session):
    """Create admin role"""
    role = Role.query.filter_by(name='admin').first()
    return role

@pytest.fixture
def customer_role(db_session):
    """Create customer role"""
    role = Role.query.filter_by(name='customer').first()
    return role

@pytest.fixture
def admin_user(db_session, admin_role):
    """Create admin user"""
    user = User(
        email='admin@test.com',
        first_name='Admin',
        last_name='User',
        role_id=admin_role.id
    )
    user.set_password('admin123')
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def customer_user(db_session, customer_role):
    """Create customer user"""
    user = User(
        email='customer@test.com',
        first_name='Customer',
        last_name='User',
        role_id=customer_role.id
    )
    user.set_password('customer123')
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def hotel(db_session):
    """Create test hotel"""
    hotel = Hotel(
        name='Test Hotel',
        address='123 Test Street',
        city='Test City',
        state='Test State',
        country='Test Country',
        postal_code='12345',
        phone='+1234567890',
        email='test@hotel.com',
        latitude=Decimal('40.7128'),
        longitude=Decimal('-74.0060'),
        amenities=['wifi', 'parking', 'pool']
    )
    db_session.add(hotel)
    db_session.commit()
    return hotel

@pytest.fixture
def room_type(db_session, hotel):
    """Create test room type"""
    room_type = RoomType(
        hotel_id=hotel.id,
        name='Standard Room',
        description='A comfortable standard room',
        max_occupancy=2,
        amenities=['wifi', 'tv'],
        base_price=Decimal('100.00'),
        pricing_rules={'weekend_multiplier': 1.2}
    )
    db_session.add(room_type)
    db_session.commit()
    return room_type

@pytest.fixture
def rooms(db_session, hotel, room_type):
    """Create test rooms"""
    rooms = []
    for i in range(1, 6):  # Create 5 rooms
        room = Room(
            hotel_id=hotel.id,
            room_type_id=room_type.id,
            room_number=f'101{i}',
            floor='1',
            features={'view': 'city', 'balcony': True}
        )
        db_session.add(room)
        rooms.append(room)
    
    db_session.commit()
    return rooms

@pytest.fixture
def guest(db_session):
    """Create test guest"""
    guest = Guest(
        first_name='John',
        last_name='Doe',
        email='john.doe@test.com',
        phone='+1234567890',
        nationality='US',
        date_of_birth=datetime(1990, 1, 1).date()
    )
    db_session.add(guest)
    db_session.commit()
    return guest

@pytest.fixture
def booking(db_session, customer_user, hotel, guest, room_type, rooms):
    """Create test booking"""
    check_in = datetime.utcnow() + timedelta(days=7)
    check_out = check_in + timedelta(days=3)
    
    booking = Booking(
        hotel_id=hotel.id,
        user_id=customer_user.id,
        guest_id=guest.id,
        check_in=check_in,
        check_out=check_out,
        adults=2,
        children=0,
        total_amount=Decimal('300.00'),
        status='confirmed',
        special_requests='Late checkout please'
    )
    db_session.add(booking)
    db_session.flush()  # Get booking ID
    
    # Create booking room
    booking_room = BookingRoom(
        booking_id=booking.id,
        room_id=rooms[0].id,
        rate=Decimal('100.00')
    )
    db_session.add(booking_room)
    db_session.commit()
    
    return booking

@pytest.fixture
def payment(db_session, booking):
    """Create test payment"""
    payment = Payment(
        booking_id=booking.id,
        payment_method='stripe',
        amount=booking.total_amount,
        currency='USD',
        status='completed',
        transaction_id='stripe_test_123',
        payment_details={
            'stripe_payment_intent_id': 'pi_test_123',
            'card_last4': '4242',
            'card_brand': 'visa'
        }
    )
    db_session.add(payment)
    db_session.commit()
    return payment

@pytest.fixture
def review(db_session, booking, customer_user):
    """Create test review"""
    review = Review(
        booking_id=booking.id,
        user_id=customer_user.id,
        rating=5,
        title='Excellent stay!',
        comment='Great hotel, excellent service!',
        is_verified=True
    )
    db_session.add(review)
    db_session.commit()
    return review

@pytest.fixture
def auth_headers(client, customer_user):
    """Get authentication headers for customer user"""
    response = client.post('/api/auth/login', json={
        'email': customer_user.email,
        'password': 'customer123'
    })
    token = response.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def admin_headers(client, admin_user):
    """Get authentication headers for admin user"""
    response = client.post('/api/auth/login', json={
        'email': admin_user.email,
        'password': 'admin123'
    })
    token = response.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def sample_booking_data():
    """Sample booking data for testing"""
    return {
        'hotel_id': 1,
        'check_in': (datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%d'),
        'check_out': (datetime.utcnow() + timedelta(days=10)).strftime('%Y-%m-%d'),
        'adults': 2,
        'children': 0,
        'room_selections': [
            {
                'room_type_id': 1,
                'quantity': 1
            }
        ],
        'guest_info': {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@test.com',
            'phone': '+1234567890',
            'nationality': 'US'
        },
        'special_requests': 'Late checkout please'
    }

@pytest.fixture
def sample_payment_data():
    """Sample payment data for testing"""
    return {
        'payment_method_id': 'pm_test_123',
        'payment_method_type': 'card',
        'card_last4': '4242',
        'card_brand': 'visa'
    }
