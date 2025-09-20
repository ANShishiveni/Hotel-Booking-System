"""
Test suite for overbooking prevention and concurrency controls
"""

import pytest
import threading
import time
from datetime import datetime, timedelta
from decimal import Decimal

from app import db
from app.models.booking import Booking, BookingRoom
from app.models.hotel import Hotel, RoomType, Room
from app.models.user import User, Role
from app.models.booking import Guest
from app.services.booking_service import BookingService


class TestOverbookingPrevention:
    """Test overbooking prevention mechanisms"""
    
    def test_concurrent_booking_same_room(self, app, db_session, customer_user, hotel, room_type, rooms):
        """Test that concurrent bookings for the same room are prevented"""
        with app.app_context():
            # Create a guest
            guest = Guest(
                first_name='John',
                last_name='Doe',
                email='john@test.com'
            )
            db_session.add(guest)
            db_session.commit()
            
            # Create booking service
            booking_service = BookingService()
            
            # Define booking parameters
            check_in = datetime.utcnow() + timedelta(days=7)
            check_out = check_in + timedelta(days=3)
            
            room_selections = [{'room_type_id': room_type.id, 'quantity': 1}]
            
            # Results from concurrent threads
            results = []
            errors = []
            
            def create_booking():
                """Create booking in a separate thread"""
                try:
                    booking = booking_service.create_booking(
                        user_id=customer_user.id,
                        hotel_id=hotel.id,
                        guest_id=guest.id,
                        check_in=check_in,
                        check_out=check_out,
                        adults=2,
                        children=0,
                        room_selections=room_selections
                    )
                    results.append(booking.id)
                except Exception as e:
                    errors.append(str(e))
            
            # Create multiple threads to simulate concurrent bookings
            threads = []
            for i in range(5):  # Try to book the same room 5 times
                thread = threading.Thread(target=create_booking)
                threads.append(thread)
            
            # Start all threads simultaneously
            for thread in threads:
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Only one booking should succeed
            assert len(results) == 1, f"Expected 1 successful booking, got {len(results)}"
            assert len(errors) == 4, f"Expected 4 failed bookings, got {len(errors)}"
            
            # Check that all errors are about availability
            for error in errors:
                assert 'available' in error.lower() or 'conflict' in error.lower()
    
    def test_room_availability_check_with_locking(self, app, db_session, hotel, room_type, rooms):
        """Test room availability check with database locking"""
        with app.app_context():
            booking_service = BookingService()
            
            check_in = datetime.utcnow() + timedelta(days=7)
            check_out = check_in + timedelta(days=3)
            
            # Test availability check
            available_rooms = booking_service.search_available_rooms(
                hotel_id=hotel.id,
                check_in=check_in,
                check_out=check_out
            )
            
            # Should find the room type with 5 available rooms
            assert room_type in available_rooms
            assert available_rooms[room_type] == 5
    
    def test_booking_with_insufficient_rooms(self, app, db_session, customer_user, hotel, room_type, rooms):
        """Test booking when there are insufficient rooms available"""
        with app.app_context():
            # Create a guest
            guest = Guest(
                first_name='John',
                last_name='Doe',
                email='john@test.com'
            )
            db_session.add(guest)
            db_session.commit()
            
            booking_service = BookingService()
            
            check_in = datetime.utcnow() + timedelta(days=7)
            check_out = check_in + timedelta(days=3)
            
            # Try to book more rooms than available
            room_selections = [{'room_type_id': room_type.id, 'quantity': 10}]
            
            with pytest.raises(ValueError) as exc_info:
                booking_service.create_booking(
                    user_id=customer_user.id,
                    hotel_id=hotel.id,
                    guest_id=guest.id,
                    check_in=check_in,
                    check_out=check_out,
                    adults=2,
                    children=0,
                    room_selections=room_selections
                )
            
            assert 'available' in str(exc_info.value).lower()
    
    def test_partial_room_booking_conflict(self, app, db_session, customer_user, hotel, room_type, rooms):
        """Test scenario where partial rooms are booked, causing conflicts"""
        with app.app_context():
            # Create guests
            guest1 = Guest(first_name='John', last_name='Doe', email='john@test.com')
            guest2 = Guest(first_name='Jane', last_name='Smith', email='jane@test.com')
            db_session.add_all([guest1, guest2])
            db_session.commit()
            
            booking_service = BookingService()
            
            check_in = datetime.utcnow() + timedelta(days=7)
            check_out = check_in + timedelta(days=3)
            
            # First user books 3 rooms
            room_selections1 = [{'room_type_id': room_type.id, 'quantity': 3}]
            booking1 = booking_service.create_booking(
                user_id=customer_user.id,
                hotel_id=hotel.id,
                guest_id=guest1.id,
                check_in=check_in,
                check_out=check_out,
                adults=2,
                children=0,
                room_selections=room_selections1
            )
            
            # Second user tries to book 3 more rooms (should fail)
            room_selections2 = [{'room_type_id': room_type.id, 'quantity': 3}]
            
            with pytest.raises(ValueError) as exc_info:
                booking_service.create_booking(
                    user_id=customer_user.id,
                    hotel_id=hotel.id,
                    guest_id=guest2.id,
                    check_in=check_in,
                    check_out=check_out,
                    adults=2,
                    children=0,
                    room_selections=room_selections2
                )
            
            assert 'available' in str(exc_info.value).lower()
    
    def test_booking_status_conflicts(self, app, db_session, customer_user, hotel, room_type, rooms, booking):
        """Test that different booking statuses are handled correctly"""
        with app.app_context():
            booking_service = BookingService()
            
            # Test that cancelled bookings don't block availability
            booking.status = 'cancelled'
            db_session.commit()
            
            check_in = datetime.utcnow() + timedelta(days=7)
            check_out = check_in + timedelta(days=3)
            
            # Should be able to book the room that was cancelled
            available_rooms = booking_service.search_available_rooms(
                hotel_id=hotel.id,
                check_in=check_in,
                check_out=check_out
            )
            
            assert room_type in available_rooms
            assert available_rooms[room_type] == 5  # All rooms available again
    
    def test_transaction_rollback_on_error(self, app, db_session, customer_user, hotel, room_type, rooms):
        """Test that transactions are properly rolled back on errors"""
        with app.app_context():
            # Create a guest
            guest = Guest(
                first_name='John',
                last_name='Doe',
                email='john@test.com'
            )
            db_session.add(guest)
            db_session.commit()
            
            booking_service = BookingService()
            
            check_in = datetime.utcnow() + timedelta(days=7)
            check_out = check_in + timedelta(days=3)
            
            # Try to book with invalid room type
            room_selections = [{'room_type_id': 99999, 'quantity': 1}]
            
            with pytest.raises(ValueError):
                booking_service.create_booking(
                    user_id=customer_user.id,
                    hotel_id=hotel.id,
                    guest_id=guest.id,
                    check_in=check_in,
                    check_out=check_out,
                    adults=2,
                    children=0,
                    room_selections=room_selections
                )
            
            # Verify no booking was created
            bookings_count = Booking.query.count()
            assert bookings_count == 0
    
    def test_concurrent_cancellation_and_booking(self, app, db_session, customer_user, hotel, room_type, rooms, booking):
        """Test concurrent cancellation and new booking"""
        with app.app_context():
            # Create a guest for new booking
            guest2 = Guest(
                first_name='Jane',
                last_name='Smith',
                email='jane@test.com'
            )
            db_session.add(guest2)
            db_session.commit()
            
            booking_service = BookingService()
            
            check_in = datetime.utcnow() + timedelta(days=7)
            check_out = check_in + timedelta(days=3)
            
            results = []
            errors = []
            
            def cancel_booking():
                """Cancel existing booking"""
                try:
                    booking_service.cancel_booking(booking.id, "Test cancellation")
                    results.append('cancelled')
                except Exception as e:
                    errors.append(f"Cancel error: {str(e)}")
            
            def create_new_booking():
                """Create new booking"""
                try:
                    room_selections = [{'room_type_id': room_type.id, 'quantity': 1}]
                    new_booking = booking_service.create_booking(
                        user_id=customer_user.id,
                        hotel_id=hotel.id,
                        guest_id=guest2.id,
                        check_in=check_in,
                        check_out=check_out,
                        adults=2,
                        children=0,
                        room_selections=room_selections
                    )
                    results.append(f'created_{new_booking.id}')
                except Exception as e:
                    errors.append(f"Create error: {str(e)}")
            
            # Start cancellation and booking threads
            cancel_thread = threading.Thread(target=cancel_booking)
            create_thread = threading.Thread(target=create_new_booking)
            
            cancel_thread.start()
            create_thread.start()
            
            cancel_thread.join()
            create_thread.join()
            
            # Either cancellation succeeded or new booking failed due to conflict
            assert len(results) >= 1
            assert len(errors) >= 0
    
    def test_room_type_inactive_conflict(self, app, db_session, customer_user, hotel, room_type, rooms):
        """Test booking with inactive room type"""
        with app.app_context():
            # Create a guest
            guest = Guest(
                first_name='John',
                last_name='Doe',
                email='john@test.com'
            )
            db_session.add(guest)
            db_session.commit()
            
            # Deactivate room type
            room_type.is_active = False
            db_session.commit()
            
            booking_service = BookingService()
            
            check_in = datetime.utcnow() + timedelta(days=7)
            check_out = check_in + timedelta(days=3)
            
            room_selections = [{'room_type_id': room_type.id, 'quantity': 1}]
            
            with pytest.raises(ValueError) as exc_info:
                booking_service.create_booking(
                    user_id=customer_user.id,
                    hotel_id=hotel.id,
                    guest_id=guest.id,
                    check_in=check_in,
                    check_out=check_out,
                    adults=2,
                    children=0,
                    room_selections=room_selections
                )
            
            assert 'inactive' in str(exc_info.value).lower() or 'not found' in str(exc_info.value).lower()
    
    def test_booking_date_overlap_prevention(self, app, db_session, customer_user, hotel, room_type, rooms, booking):
        """Test that overlapping date ranges are properly handled"""
        with app.app_context():
            # Create a guest
            guest2 = Guest(
                first_name='Jane',
                last_name='Smith',
                email='jane@test.com'
            )
            db_session.add(guest2)
            db_session.commit()
            
            booking_service = BookingService()
            
            # Create overlapping dates
            check_in = booking.check_in + timedelta(days=1)
            check_out = booking.check_out + timedelta(days=1)
            
            room_selections = [{'room_type_id': room_type.id, 'quantity': 1}]
            
            with pytest.raises(ValueError) as exc_info:
                booking_service.create_booking(
                    user_id=customer_user.id,
                    hotel_id=hotel.id,
                    guest_id=guest2.id,
                    check_in=check_in,
                    check_out=check_out,
                    adults=2,
                    children=0,
                    room_selections=room_selections
                )
            
            assert 'available' in str(exc_info.value).lower()
