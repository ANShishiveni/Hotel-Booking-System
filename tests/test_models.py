import pytest
from datetime import datetime, date, timedelta
from app import create_app, db
from app.models import User, Hotel, RoomType, Room, Booking, Guest, Payment, Review, Role
from config import TestingConfig

class TestModels:
    """Test suite for database models"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup test database for each test"""
        self.app = create_app('TestingConfig')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        yield
        
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_user_creation(self):
        """Test user model creation and password hashing"""
        user = User(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User'
        )
        user.set_password('password123')
        
        db.session.add(user)
        db.session.commit()
        
        assert user.id is not None
        assert user.check_password('password123')
        assert not user.check_password('wrongpassword')
        assert user.password_hash != 'password123'
    
    def test_user_to_dict(self):
        """Test user serialization"""
        user = User(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User',
            phone='+264123456789'
        )
        user.set_password('password123')
        
        db.session.add(user)
        db.session.commit()
        
        user_dict = user.to_dict()
        
        assert user_dict['email'] == 'test@example.com'
        assert user_dict['username'] == 'testuser'
        assert user_dict['first_name'] == 'Test'
        assert user_dict['last_name'] == 'User'
        assert user_dict['phone'] == '+264123456789'
        assert 'password_hash' not in user_dict
    
    def test_hotel_creation(self):
        """Test hotel model creation"""
        hotel = Hotel(
            name='Test Hotel',
            description='A test hotel',
            address='123 Test Street',
            city='Windhoek',
            country='Namibia',
            star_rating=4,
            amenities=['WiFi', 'Pool', 'Restaurant'],
            images=['image1.jpg', 'image2.jpg']
        )
        
        db.session.add(hotel)
        db.session.commit()
        
        assert hotel.id is not None
        assert hotel.name == 'Test Hotel'
        assert hotel.amenities == ['WiFi', 'Pool', 'Restaurant']
        assert hotel.images == ['image1.jpg', 'image2.jpg']
    
    def test_room_type_creation(self):
        """Test room type model creation"""
        hotel = Hotel(
            name='Test Hotel',
            address='123 Test Street',
            city='Windhoek',
            country='Namibia'
        )
        db.session.add(hotel)
        db.session.commit()
        
        room_type = RoomType(
            hotel_id=hotel.id,
            name='Standard Room',
            description='A standard room',
            base_price=100.00,
            max_occupancy=2,
            bed_type='Queen',
            room_size=25
        )
        
        db.session.add(room_type)
        db.session.commit()
        
        assert room_type.id is not None
        assert room_type.hotel_id == hotel.id
        assert room_type.base_price == 100.00
        assert room_type.max_occupancy == 2
    
    def test_room_creation(self):
        """Test room model creation"""
        hotel = Hotel(
            name='Test Hotel',
            address='123 Test Street',
            city='Windhoek',
            country='Namibia'
        )
        db.session.add(hotel)
        
        room_type = RoomType(
            hotel_id=hotel.id,
            name='Standard Room',
            base_price=100.00,
            max_occupancy=2
        )
        db.session.add(room_type)
        db.session.commit()
        
        room = Room(
            hotel_id=hotel.id,
            room_type_id=room_type.id,
            room_number='101',
            floor=1
        )
        
        db.session.add(room)
        db.session.commit()
        
        assert room.id is not None
        assert room.room_number == '101'
        assert room.floor == 1
        assert room.hotel_id == hotel.id
        assert room.room_type_id == room_type.id
    
    def test_booking_creation(self):
        """Test booking model creation"""
        # Create user
        user = User(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User'
        )
        user.set_password('password123')
        db.session.add(user)
        
        # Create hotel
        hotel = Hotel(
            name='Test Hotel',
            address='123 Test Street',
            city='Windhoek',
            country='Namibia'
        )
        db.session.add(hotel)
        
        # Create room type
        room_type = RoomType(
            hotel_id=hotel.id,
            name='Standard Room',
            base_price=100.00,
            max_occupancy=2
        )
        db.session.add(room_type)
        
        # Create room
        room = Room(
            hotel_id=hotel.id,
            room_type_id=room_type.id,
            room_number='101'
        )
        db.session.add(room)
        db.session.commit()
        
        # Create booking
        check_in = date.today() + timedelta(days=7)
        check_out = check_in + timedelta(days=2)
        
        booking = Booking(
            booking_reference=Booking().generate_booking_reference(),
            user_id=user.id,
            hotel_id=hotel.id,
            room_id=room.id,
            room_type_id=room_type.id,
            check_in_date=check_in,
            check_out_date=check_out,
            nights=2,
            adults=2,
            children=0,
            room_rate=100.00,
            total_amount=200.00,
            tax_amount=30.00,
            discount_amount=0,
            status='pending'
        )
        
        db.session.add(booking)
        db.session.commit()
        
        assert booking.id is not None
        assert booking.booking_reference.startswith('BK')
        assert booking.user_id == user.id
        assert booking.hotel_id == hotel.id
        assert booking.room_id == room.id
        assert booking.nights == 2
        assert booking.total_amount == 200.00
        assert booking.status == 'pending'
    
    def test_guest_creation(self):
        """Test guest model creation"""
        # Create booking first
        user = User(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User'
        )
        user.set_password('password123')
        db.session.add(user)
        
        hotel = Hotel(
            name='Test Hotel',
            address='123 Test Street',
            city='Windhoek',
            country='Namibia'
        )
        db.session.add(hotel)
        
        room_type = RoomType(
            hotel_id=hotel.id,
            name='Standard Room',
            base_price=100.00,
            max_occupancy=2
        )
        db.session.add(room_type)
        
        room = Room(
            hotel_id=hotel.id,
            room_type_id=room_type.id,
            room_number='101'
        )
        db.session.add(room)
        
        booking = Booking(
            booking_reference=Booking().generate_booking_reference(),
            user_id=user.id,
            hotel_id=hotel.id,
            room_id=room.id,
            room_type_id=room_type.id,
            check_in_date=date.today() + timedelta(days=7),
            check_out_date=date.today() + timedelta(days=9),
            nights=2,
            adults=2,
            children=0,
            room_rate=100.00,
            total_amount=200.00,
            status='pending'
        )
        db.session.add(booking)
        db.session.commit()
        
        # Create guest
        guest = Guest(
            booking_id=booking.id,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone='+264123456789',
            is_primary_guest=True
        )
        
        db.session.add(guest)
        db.session.commit()
        
        assert guest.id is not None
        assert guest.booking_id == booking.id
        assert guest.first_name == 'John'
        assert guest.last_name == 'Doe'
        assert guest.email == 'john@example.com'
        assert guest.is_primary_guest == True
    
    def test_payment_creation(self):
        """Test payment model creation"""
        # Create booking first
        user = User(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User'
        )
        user.set_password('password123')
        db.session.add(user)
        
        hotel = Hotel(
            name='Test Hotel',
            address='123 Test Street',
            city='Windhoek',
            country='Namibia'
        )
        db.session.add(hotel)
        
        room_type = RoomType(
            hotel_id=hotel.id,
            name='Standard Room',
            base_price=100.00,
            max_occupancy=2
        )
        db.session.add(room_type)
        
        room = Room(
            hotel_id=hotel.id,
            room_type_id=room_type.id,
            room_number='101'
        )
        db.session.add(room)
        
        booking = Booking(
            booking_reference=Booking().generate_booking_reference(),
            user_id=user.id,
            hotel_id=hotel.id,
            room_id=room.id,
            room_type_id=room_type.id,
            check_in_date=date.today() + timedelta(days=7),
            check_out_date=date.today() + timedelta(days=9),
            nights=2,
            adults=2,
            children=0,
            room_rate=100.00,
            total_amount=200.00,
            status='pending'
        )
        db.session.add(booking)
        db.session.commit()
        
        # Create payment
        payment = Payment(
            booking_id=booking.id,
            payment_reference=Payment().generate_payment_reference(),
            amount=200.00,
            currency='NAD',
            payment_method='card',
            payment_provider='stripe',
            status='pending',
            payment_intent_id='pi_test123'
        )
        
        db.session.add(payment)
        db.session.commit()
        
        assert payment.id is not None
        assert payment.booking_id == booking.id
        assert payment.payment_reference.startswith('PAY')
        assert payment.amount == 200.00
        assert payment.currency == 'NAD'
        assert payment.payment_method == 'card'
        assert payment.status == 'pending'
    
    def test_review_creation(self):
        """Test review model creation"""
        # Create user
        user = User(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User'
        )
        user.set_password('password123')
        db.session.add(user)
        
        # Create hotel
        hotel = Hotel(
            name='Test Hotel',
            address='123 Test Street',
            city='Windhoek',
            country='Namibia'
        )
        db.session.add(hotel)
        
        # Create booking
        room_type = RoomType(
            hotel_id=hotel.id,
            name='Standard Room',
            base_price=100.00,
            max_occupancy=2
        )
        db.session.add(room_type)
        
        room = Room(
            hotel_id=hotel.id,
            room_type_id=room_type.id,
            room_number='101'
        )
        db.session.add(room)
        
        booking = Booking(
            booking_reference=Booking().generate_booking_reference(),
            user_id=user.id,
            hotel_id=hotel.id,
            room_id=room.id,
            room_type_id=room_type.id,
            check_in_date=date.today() - timedelta(days=7),
            check_out_date=date.today() - timedelta(days=5),
            nights=2,
            adults=2,
            children=0,
            room_rate=100.00,
            total_amount=200.00,
            status='checked_out'
        )
        db.session.add(booking)
        db.session.commit()
        
        # Create review
        review = Review(
            hotel_id=hotel.id,
            user_id=user.id,
            booking_id=booking.id,
            rating=5,
            title='Excellent stay!',
            comment='Great hotel with amazing service.',
            is_verified=True
        )
        
        db.session.add(review)
        db.session.commit()
        
        assert review.id is not None
        assert review.hotel_id == hotel.id
        assert review.user_id == user.id
        assert review.booking_id == booking.id
        assert review.rating == 5
        assert review.title == 'Excellent stay!'
        assert review.is_verified == True
    
    def test_role_assignment(self):
        """Test user role assignment"""
        # Create roles
        guest_role = Role(name='guest', description='Guest user')
        admin_role = Role(name='admin', description='Administrator')
        
        db.session.add(guest_role)
        db.session.add(admin_role)
        
        # Create user
        user = User(
            email='admin@example.com',
            username='admin',
            first_name='Admin',
            last_name='User'
        )
        user.set_password('password123')
        user.roles.extend([guest_role, admin_role])
        
        db.session.add(user)
        db.session.commit()
        
        assert user.has_role('guest')
        assert user.has_role('admin')
        assert not user.has_role('staff')
        
        # Test permissions
        permissions = user.get_permissions()
        assert isinstance(permissions, list)
    
    def test_hotel_average_rating(self):
        """Test hotel average rating calculation"""
        # Create hotel
        hotel = Hotel(
            name='Test Hotel',
            address='123 Test Street',
            city='Windhoek',
            country='Namibia'
        )
        db.session.add(hotel)
        
        # Create users for reviews
        user1 = User(
            email='user1@example.com',
            username='user1',
            first_name='User',
            last_name='One'
        )
        user1.set_password('password123')
        
        user2 = User(
            email='user2@example.com',
            username='user2',
            first_name='User',
            last_name='Two'
        )
        user2.set_password('password123')
        
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        
        # Create reviews
        review1 = Review(
            hotel_id=hotel.id,
            user_id=user1.id,
            rating=4,
            comment='Good hotel',
            is_active=True
        )
        
        review2 = Review(
            hotel_id=hotel.id,
            user_id=user2.id,
            rating=5,
            comment='Excellent hotel',
            is_active=True
        )
        
        db.session.add(review1)
        db.session.add(review2)
        db.session.commit()
        
        # Test average rating
        average_rating = hotel.get_average_rating()
        assert average_rating == 4.5
        
        # Test with no reviews
        hotel2 = Hotel(
            name='Test Hotel 2',
            address='456 Test Street',
            city='Swakopmund',
            country='Namibia'
        )
        db.session.add(hotel2)
        db.session.commit()
        
        assert hotel2.get_average_rating() == 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
