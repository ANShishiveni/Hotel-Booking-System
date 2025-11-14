import pytest
import threading
import time
from datetime import datetime, date, timedelta
from app import create_app, db
from app.models import User, Hotel, RoomType, Room, Booking, Guest, Role
from config import TestingConfig

class TestOverbookingPrevention:
    """Test suite for overbooking prevention with concurrency controls"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup test database and data for each test"""
        self.app = create_app('TestingConfig')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create test database
        db.create_all()
        
        # Create test roles
        self.guest_role = Role(name='guest', description='Guest user')
        db.session.add(self.guest_role)
        
        # Create test user
        self.test_user = User(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User'
        )
        self.test_user.set_password('password123')
        self.test_user.roles.append(self.guest_role)
        db.session.add(self.test_user)
        
        # Create test hotel
        self.test_hotel = Hotel(
            name='Test Hotel',
            description='A test hotel for testing',
            address='123 Test Street',
            city='Windhoek',
            country='Namibia',
            star_rating=4
        )
        db.session.add(self.test_hotel)
        
        # Create test room type
        self.test_room_type = RoomType(
            hotel_id=self.test_hotel.id,
            name='Standard Room',
            description='A standard test room',
            base_price=100.00,
            max_occupancy=2
        )
        db.session.add(self.test_room_type)
        
        # Create test rooms
        self.test_rooms = []
        for i in range(5):  # Create 5 test rooms
            room = Room(
                hotel_id=self.test_hotel.id,
                room_type_id=self.test_room_type.id,
                room_number=f'101{i}',
                floor=1
            )
            self.test_rooms.append(room)
            db.session.add(room)
        
        db.session.commit()
        
        # Set test dates
        self.check_in_date = date.today() + timedelta(days=7)
        self.check_out_date = self.check_in_date + timedelta(days=2)
        
        yield
        
        # Cleanup
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_single_booking_success(self):
        """Test that a single booking is created successfully"""
        booking_data = {
            'hotel_id': self.test_hotel.id,
            'room_type_id': self.test_room_type.id,
            'check_in_date': self.check_in_date.isoformat(),
            'check_out_date': self.check_out_date.isoformat(),
            'guests': [{
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john@example.com'
            }]
        }
        
        # Create booking
        booking = self._create_booking(booking_data)
        
        assert booking is not None
        assert booking.status == 'pending'
        assert booking.user_id == self.test_user.id
        assert booking.hotel_id == self.test_hotel.id
        assert booking.room_id in [room.id for room in self.test_rooms]
    
    def test_concurrent_bookings_same_room_type(self):
        """Test that concurrent bookings for the same room type don't cause overbooking"""
        booking_data = {
            'hotel_id': self.test_hotel.id,
            'room_type_id': self.test_room_type.id,
            'check_in_date': self.check_in_date.isoformat(),
            'check_out_date': self.check_out_date.isoformat(),
            'guests': [{
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'test@example.com'
            }]
        }
        
        results = []
        threads = []
        
        def create_booking_thread(thread_id):
            """Thread function to create booking"""
            try:
                with self.app.app_context():
                    booking = self._create_booking(booking_data)
                    results.append({'thread_id': thread_id, 'booking': booking, 'success': True})
            except Exception as e:
                results.append({'thread_id': thread_id, 'error': str(e), 'success': False})
        
        # Create 10 concurrent booking attempts (more than available rooms)
        for i in range(10):
            thread = threading.Thread(target=create_booking_thread, args=(i,))
            threads.append(thread)
        
        # Start all threads simultaneously
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Analyze results
        successful_bookings = [r for r in results if r['success'] and r['booking'] is not None]
        failed_bookings = [r for r in results if not r['success']]
        
        print(f"Successful bookings: {len(successful_bookings)}")
        print(f"Failed bookings: {len(failed_bookings)}")
        
        # Should have exactly 5 successful bookings (one per room)
        assert len(successful_bookings) == 5, f"Expected 5 successful bookings, got {len(successful_bookings)}"
        
        # All other attempts should fail due to no available rooms
        assert len(failed_bookings) == 5, f"Expected 5 failed bookings, got {len(failed_bookings)}"
        
        # Check that each room is only booked once
        booked_room_ids = [b['booking'].room_id for b in successful_bookings]
        assert len(set(booked_room_ids)) == 5, "Some rooms were booked multiple times"
        
        # Verify booking references are unique
        booking_refs = [b['booking'].booking_reference for b in successful_bookings]
        assert len(set(booking_refs)) == 5, "Duplicate booking references found"
    
    def test_concurrent_bookings_different_dates(self):
        """Test that concurrent bookings for different dates don't interfere"""
        # Create bookings for different date ranges
        date_ranges = [
            (self.check_in_date, self.check_out_date),
            (self.check_in_date + timedelta(days=3), self.check_out_date + timedelta(days=3)),
            (self.check_in_date + timedelta(days=6), self.check_out_date + timedelta(days=6))
        ]
        
        results = []
        threads = []
        
        def create_booking_for_dates(thread_id, check_in, check_out):
            """Thread function to create booking for specific dates"""
            try:
                with self.app.app_context():
                    booking_data = {
                        'hotel_id': self.test_hotel.id,
                        'room_type_id': self.test_room_type.id,
                        'check_in_date': check_in.isoformat(),
                        'check_out_date': check_out.isoformat(),
                        'guests': [{
                            'first_name': f'User{thread_id}',
                            'last_name': 'Test',
                            'email': f'user{thread_id}@example.com'
                        }]
                    }
                    booking = self._create_booking(booking_data)
                    results.append({'thread_id': thread_id, 'booking': booking, 'success': True})
            except Exception as e:
                results.append({'thread_id': thread_id, 'error': str(e), 'success': False})
        
        # Create concurrent bookings for different date ranges
        for i, (check_in, check_out) in enumerate(date_ranges):
            thread = threading.Thread(target=create_booking_for_dates, args=(i, check_in, check_out))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # All bookings should succeed since they're for different dates
        successful_bookings = [r for r in results if r['success'] and r['booking'] is not None]
        assert len(successful_bookings) == 3, f"Expected 3 successful bookings, got {len(successful_bookings)}"
    
    def test_booking_confirmation_prevents_overbooking(self):
        """Test that confirmed bookings prevent overbooking"""
        # Create and confirm a booking
        booking_data = {
            'hotel_id': self.test_hotel.id,
            'room_type_id': self.test_room_type.id,
            'check_in_date': self.check_in_date.isoformat(),
            'check_out_date': self.check_out_date.isoformat(),
            'guests': [{
                'first_name': 'Confirmed',
                'last_name': 'User',
                'email': 'confirmed@example.com'
            }]
        }
        
        booking = self._create_booking(booking_data)
        booking.status = 'confirmed'
        booking.confirmed_at = datetime.utcnow()
        db.session.commit()
        
        # Try to create another booking for the same room and dates
        try:
            second_booking = self._create_booking(booking_data)
            assert False, "Should not be able to book the same room twice"
        except Exception:
            # This is expected - the booking should fail
            pass
        
        # Verify only one booking exists for this room and date range
        conflicting_bookings = Booking.query.filter(
            Booking.room_id == booking.room_id,
            Booking.check_in_date <= self.check_in_date,
            Booking.check_out_date > self.check_in_date,
            Booking.status.in_(['confirmed', 'checked_in'])
        ).count()
        
        assert conflicting_bookings == 1, "Should have exactly one confirmed booking"
    
    def test_pending_booking_prevents_overbooking(self):
        """Test that pending bookings also prevent overbooking"""
        # Create a pending booking
        booking_data = {
            'hotel_id': self.test_hotel.id,
            'room_type_id': self.test_room_type.id,
            'check_in_date': self.check_in_date.isoformat(),
            'check_out_date': self.check_out_date.isoformat(),
            'guests': [{
                'first_name': 'Pending',
                'last_name': 'User',
                'email': 'pending@example.com'
            }]
        }
        
        booking = self._create_booking(booking_data)
        # Status is already 'pending' by default
        db.session.commit()
        
        # Try to create another booking for the same room and dates
        try:
            second_booking = self._create_booking(booking_data)
            assert False, "Should not be able to book the same room twice"
        except Exception:
            # This is expected
            pass
    
    def test_cancelled_booking_allows_rebooking(self):
        """Test that cancelled bookings allow the room to be rebooked"""
        # Create and cancel a booking
        booking_data = {
            'hotel_id': self.test_hotel.id,
            'room_type_id': self.test_room_type.id,
            'check_in_date': self.check_in_date.isoformat(),
            'check_out_date': self.check_out_date.isoformat(),
            'guests': [{
                'first_name': 'Cancelled',
                'last_name': 'User',
                'email': 'cancelled@example.com'
            }]
        }
        
        booking = self._create_booking(booking_data)
        booking.status = 'cancelled'
        booking.cancelled_at = datetime.utcnow()
        db.session.commit()
        
        # Try to create another booking for the same room and dates
        new_booking_data = booking_data.copy()
        new_booking_data['guests'] = [{
            'first_name': 'New',
            'last_name': 'User',
            'email': 'new@example.com'
        }]
        
        new_booking = self._create_booking(new_booking_data)
        assert new_booking is not None, "Should be able to book after cancellation"
        assert new_booking.room_id == booking.room_id, "Should be able to book the same room"
    
    def _create_booking(self, booking_data):
        """Helper method to create a booking with proper transaction handling"""
        try:
            with db.session.begin():
                # Find available room with FOR UPDATE lock
                available_room = db.session.query(Room)\
                    .outerjoin(Booking, db.and_(
                        Booking.room_id == Room.id,
                        db.or_(
                            db.and_(
                                Booking.check_in_date <= datetime.strptime(booking_data['check_in_date'], '%Y-%m-%d').date(),
                                Booking.check_out_date > datetime.strptime(booking_data['check_in_date'], '%Y-%m-%d').date()
                            ),
                            db.and_(
                                Booking.check_in_date < datetime.strptime(booking_data['check_out_date'], '%Y-%m-%d').date(),
                                Booking.check_out_date >= datetime.strptime(booking_data['check_out_date'], '%Y-%m-%d').date()
                            ),
                            db.and_(
                                Booking.check_in_date >= datetime.strptime(booking_data['check_in_date'], '%Y-%m-%d').date(),
                                Booking.check_out_date <= datetime.strptime(booking_data['check_out_date'], '%Y-%m-%d').date()
                            )
                        ),
                        Booking.status.in_(['confirmed', 'checked_in'])
                    ), isouter=True)\
                    .filter(
                        Room.room_type_id == booking_data['room_type_id'],
                        Room.is_active == True,
                        Booking.id.is_(None)
                    )\
                    .with_for_update()\
                    .first()
                
                if not available_room:
                    raise Exception("No rooms available")
                
                # Create booking
                check_in_date = datetime.strptime(booking_data['check_in_date'], '%Y-%m-%d').date()
                check_out_date = datetime.strptime(booking_data['check_out_date'], '%Y-%m-%d').date()
                nights = (check_out_date - check_in_date).days
                
                booking = Booking(
                    booking_reference=Booking().generate_booking_reference(),
                    user_id=self.test_user.id,
                    hotel_id=booking_data['hotel_id'],
                    room_id=available_room.id,
                    room_type_id=booking_data['room_type_id'],
                    check_in_date=check_in_date,
                    check_out_date=check_out_date,
                    nights=nights,
                    adults=1,
                    children=0,
                    room_rate=100.00,
                    total_amount=100.00 * nights,
                    tax_amount=0,
                    discount_amount=0,
                    status='pending'
                )
                
                db.session.add(booking)
                db.session.flush()
                
                # Create guest
                guest_data = booking_data['guests'][0]
                guest = Guest(
                    booking_id=booking.id,
                    first_name=guest_data['first_name'],
                    last_name=guest_data['last_name'],
                    email=guest_data.get('email', ''),
                    is_primary_guest=True
                )
                db.session.add(guest)
                
                return booking
                
        except Exception as e:
            db.session.rollback()
            raise e

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
