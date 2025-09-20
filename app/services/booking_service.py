"""
Booking service with concurrency controls and timezone-aware logic
"""

from app import db
from app.models.booking import Booking, BookingRoom, Guest
from app.models.hotel import Hotel, Room, RoomType
from app.models.audit import AuditLog
from app.utils.timezone_utils import convert_to_utc, get_local_date_range
from app.utils.validators import validate_room_selection, validate_guest_info
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

class BookingService:
    """Service class for handling booking operations with concurrency controls"""
    
    def __init__(self):
        self.logger = logger
    
    def search_available_rooms(self, hotel_id, check_in, check_out, adults=1, children=0):
        """Search for available rooms with concurrency control"""
        try:
            # Convert dates to UTC if needed
            if isinstance(check_in, str):
                check_in = datetime.strptime(check_in, '%Y-%m-%d')
            if isinstance(check_out, str):
                check_out = datetime.strptime(check_out, '%Y-%m-%d')
            
            # Ensure dates are timezone-aware
            if check_in.tzinfo is None:
                check_in = check_in.replace(tzinfo=pytz.UTC)
            if check_out.tzinfo is None:
                check_out = check_out.replace(tzinfo=pytz.UTC)
            
            # Get all room types for the hotel
            room_types = RoomType.query.filter_by(
                hotel_id=hotel_id,
                is_active=True
            ).all()
            
            available_rooms = {}
            
            for room_type in room_types:
                # Check if room type can accommodate the occupancy
                total_occupancy = adults + children
                if room_type.max_occupancy < total_occupancy:
                    continue
                
                # Count available rooms for this type
                available_count = self._count_available_rooms(
                    room_type.id, check_in, check_out
                )
                
                if available_count > 0:
                    available_rooms[room_type] = available_count
            
            return available_rooms
            
        except Exception as e:
            self.logger.error(f"Error searching available rooms: {str(e)}")
            raise
    
    def _count_available_rooms(self, room_type_id, check_in, check_out):
        """Count available rooms for a specific room type and date range"""
        try:
            # Use a subquery to find rooms that are NOT booked during the period
            booked_room_ids = db.session.query(BookingRoom.room_id).join(Booking).filter(
                and_(
                    Room.room_type_id == room_type_id,
                    Booking.status.in_(['confirmed', 'checked_in']),
                    or_(
                        and_(
                            Booking.check_in < check_out,
                            Booking.check_out > check_in
                        )
                    )
                )
            ).subquery()
            
            # Count available rooms
            available_count = db.session.query(Room).filter(
                and_(
                    Room.room_type_id == room_type_id,
                    Room.is_active == True,
                    ~Room.id.in_(booked_room_ids)
                )
            ).count()
            
            return available_count
            
        except Exception as e:
            self.logger.error(f"Error counting available rooms: {str(e)}")
            raise
    
    def create_booking(self, user_id, hotel_id, guest_id, check_in, check_out, 
                      adults, children, room_selections, special_requests=None, timezone='UTC'):
        """Create a new booking with concurrency controls"""
        
        # Start database transaction with isolation level for concurrency control
        try:
            # Validate room selections
            validation_error = validate_room_selection(room_selections)
            if validation_error:
                raise ValueError(validation_error)
            
            # Convert dates to UTC
            if isinstance(check_in, str):
                check_in = datetime.strptime(check_in, '%Y-%m-%d')
            if isinstance(check_out, str):
                check_out = datetime.strptime(check_out, '%Y-%m-%d')
            
            # Ensure dates are timezone-aware and convert to UTC
            if check_in.tzinfo is None:
                check_in = check_in.replace(tzinfo=pytz.timezone(timezone))
            if check_out.tzinfo is None:
                check_out = check_out.replace(tzinfo=pytz.timezone(timezone))
            
            check_in_utc = convert_to_utc(check_in, timezone)
            check_out_utc = convert_to_utc(check_out, timezone)
            
            # Begin transaction with row-level locking
            with db.session.begin_nested():
                # Create booking record
                booking = Booking(
                    hotel_id=hotel_id,
                    user_id=user_id,
                    guest_id=guest_id,
                    check_in=check_in_utc,
                    check_out=check_out_utc,
                    adults=adults,
                    children=children,
                    special_requests=special_requests,
                    timezone=timezone,
                    status='pending'
                )
                
                db.session.add(booking)
                db.session.flush()  # Get booking ID
                
                # Process room selections with concurrency control
                total_amount = Decimal('0.00')
                
                for selection in room_selections:
                    room_type_id = selection['room_type_id']
                    quantity = selection['quantity']
                    
                    # Lock room type for update to prevent race conditions
                    room_type = db.session.query(RoomType).with_for_update().filter_by(
                        id=room_type_id,
                        is_active=True
                    ).first()
                    
                    if not room_type:
                        raise ValueError(f"Room type {room_type_id} not found or inactive")
                    
                    # Check availability again with lock
                    available_count = self._count_available_rooms(
                        room_type_id, check_in_utc, check_out_utc
                    )
                    
                    if available_count < quantity:
                        raise ValueError(
                            f"Only {available_count} rooms available for {room_type.name}, "
                            f"requested {quantity}"
                        )
                    
                    # Get available rooms and assign them
                    booked_room_ids = db.session.query(BookingRoom.room_id).join(Booking).filter(
                        and_(
                            Room.room_type_id == room_type_id,
                            Booking.status.in_(['confirmed', 'checked_in']),
                            or_(
                                and_(
                                    Booking.check_in < check_out_utc,
                                    Booking.check_out > check_in_utc
                                )
                            )
                        )
                    ).subquery()
                    
                    available_rooms = db.session.query(Room).filter(
                        and_(
                            Room.room_type_id == room_type_id,
                            Room.is_active == True,
                            ~Room.id.in_(booked_room_ids)
                        )
                    ).limit(quantity).all()
                    
                    if len(available_rooms) < quantity:
                        raise ValueError(
                            f"Not enough rooms available for {room_type.name}"
                        )
                    
                    # Calculate rate for this room type
                    rate = room_type.calculate_price(
                        check_in.strftime('%Y-%m-%d'),
                        check_out.strftime('%Y-%m-%d'),
                        adults,
                        children
                    )
                    
                    # Create booking room records
                    for room in available_rooms:
                        booking_room = BookingRoom(
                            booking_id=booking.id,
                            room_id=room.id,
                            rate=rate
                        )
                        db.session.add(booking_room)
                        
                        total_amount += rate
                
                # Calculate total amount based on duration
                duration_nights = (check_out_utc - check_in_utc).days
                booking.total_amount = total_amount * duration_nights
                
                # Set booking status to confirmed
                booking.status = 'confirmed'
                
                # Commit the transaction
                db.session.commit()
                
                # Log the booking creation
                AuditLog.log_custom_action(
                    'bookings', booking.id, 'BOOKING_CREATED',
                    {'booking_reference': booking.booking_reference, 'total_amount': float(booking.total_amount)},
                    user_id
                )
                
                return booking
                
        except IntegrityError as e:
            db.session.rollback()
            self.logger.error(f"Integrity error creating booking: {str(e)}")
            raise ValueError("Booking conflict detected. Please try again.")
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error creating booking: {str(e)}")
            raise
    
    def cancel_booking(self, booking_id, reason=None):
        """Cancel a booking with proper status checks"""
        try:
            with db.session.begin_nested():
                # Lock booking for update
                booking = db.session.query(Booking).with_for_update().filter_by(
                    id=booking_id
                ).first()
                
                if not booking:
                    raise ValueError("Booking not found")
                
                if not booking.can_cancel:
                    raise ValueError("Booking cannot be cancelled")
                
                # Update booking status
                booking.status = 'cancelled'
                
                # Log the cancellation
                AuditLog.log_custom_action(
                    'bookings', booking.id, 'BOOKING_CANCELLED',
                    {'reason': reason, 'booking_reference': booking.booking_reference},
                    booking.user_id
                )
                
                db.session.commit()
                
                return booking
                
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error cancelling booking: {str(e)}")
            raise
    
    def checkin_booking(self, booking_id):
        """Check-in a booking"""
        try:
            with db.session.begin_nested():
                booking = db.session.query(Booking).with_for_update().filter_by(
                    id=booking_id
                ).first()
                
                if not booking:
                    raise ValueError("Booking not found")
                
                if booking.status != 'confirmed':
                    raise ValueError("Only confirmed bookings can be checked in")
                
                booking.status = 'checked_in'
                
                # Log the check-in
                AuditLog.log_custom_action(
                    'bookings', booking.id, 'BOOKING_CHECKED_IN',
                    {'booking_reference': booking.booking_reference},
                    None  # System action
                )
                
                db.session.commit()
                
                return booking
                
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error checking in booking: {str(e)}")
            raise
    
    def checkout_booking(self, booking_id):
        """Check-out a booking"""
        try:
            with db.session.begin_nested():
                booking = db.session.query(Booking).with_for_update().filter_by(
                    id=booking_id
                ).first()
                
                if not booking:
                    raise ValueError("Booking not found")
                
                if booking.status != 'checked_in':
                    raise ValueError("Only checked-in bookings can be checked out")
                
                booking.status = 'checked_out'
                
                # Log the check-out
                AuditLog.log_custom_action(
                    'bookings', booking.id, 'BOOKING_CHECKED_OUT',
                    {'booking_reference': booking.booking_reference},
                    None  # System action
                )
                
                db.session.commit()
                
                return booking
                
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error checking out booking: {str(e)}")
            raise
    
    def get_booking_availability_report(self, hotel_id, start_date, end_date):
        """Generate availability report for a hotel"""
        try:
            # Convert dates to UTC
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=pytz.UTC)
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=pytz.UTC)
            
            # Get all room types for the hotel
            room_types = RoomType.query.filter_by(
                hotel_id=hotel_id,
                is_active=True
            ).all()
            
            report = []
            current_date = start_date
            
            while current_date < end_date:
                next_date = current_date + timedelta(days=1)
                
                day_report = {
                    'date': current_date.strftime('%Y-%m-%d'),
                    'room_types': []
                }
                
                for room_type in room_types:
                    available_count = self._count_available_rooms(
                        room_type.id, current_date, next_date
                    )
                    
                    day_report['room_types'].append({
                        'room_type_id': room_type.id,
                        'room_type_name': room_type.name,
                        'available_rooms': available_count
                    })
                
                report.append(day_report)
                current_date = next_date
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating availability report: {str(e)}")
            raise
