"""
Booking, BookingRoom, and Guest models
"""

from app import db
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import pytz
from sqlalchemy import event, CheckConstraint
from app.models.audit import AuditLog

class Guest(db.Model):
    """Guest model for booking occupants"""
    __tablename__ = 'guests'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    nationality = db.Column(db.String(50))
    date_of_birth = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='guest', lazy='dynamic')
    
    def __repr__(self):
        return f'<Guest {self.first_name} {self.last_name}>'
    
    @property
    def full_name(self):
        """Get guest's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        """Convert guest to dictionary"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'nationality': self.nationality,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Booking(db.Model):
    """Booking model"""
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_reference = db.Column(db.String(20), unique=True, nullable=False, index=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotels.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    guest_id = db.Column(db.Integer, db.ForeignKey('guests.id'), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime, nullable=False)
    adults = db.Column(db.Integer, nullable=False, default=1)
    children = db.Column(db.Integer, default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    special_requests = db.Column(db.Text)
    timezone = db.Column(db.String(50), default='UTC')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    booking_rooms = db.relationship('BookingRoom', backref='booking', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='booking', lazy='dynamic', cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='booking', lazy='dynamic', cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('check_out > check_in', name='check_checkout_after_checkin'),
        CheckConstraint('adults > 0', name='check_adults_positive'),
        CheckConstraint('children >= 0', name='check_children_non_negative'),
        CheckConstraint('total_amount >= 0', name='check_total_amount_positive'),
        CheckConstraint("status IN ('pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled')", name='check_valid_status'),
    )
    
    def __init__(self, **kwargs):
        super(Booking, self).__init__(**kwargs)
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
    
    def generate_booking_reference(self):
        """Generate unique booking reference"""
        return f"BK{datetime.utcnow().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
    
    def __repr__(self):
        return f'<Booking {self.booking_reference}>'
    
    @property
    def duration_nights(self):
        """Calculate number of nights"""
        return (self.check_out - self.check_in).days
    
    @property
    def can_cancel(self):
        """Check if booking can be cancelled"""
        if self.status in ['cancelled', 'checked_out']:
            return False
        
        # Check cancellation policy (24 hours before check-in)
        cancellation_deadline = self.check_in - timedelta(hours=24)
        return datetime.utcnow() < cancellation_deadline
    
    @property
    def is_check_in_time(self):
        """Check if it's time for check-in"""
        return datetime.utcnow() >= self.check_in
    
    @property
    def is_check_out_time(self):
        """Check if it's time for check-out"""
        return datetime.utcnow() >= self.check_out
    
    def calculate_total_amount(self):
        """Calculate total booking amount"""
        total = Decimal('0.00')
        for booking_room in self.booking_rooms:
            total += booking_room.rate * self.duration_nights
        self.total_amount = total
        return total
    
    def to_dict(self, include_rooms=False, include_payments=False):
        """Convert booking to dictionary"""
        data = {
            'id': self.id,
            'booking_reference': self.booking_reference,
            'hotel_id': self.hotel_id,
            'hotel_name': self.hotel.name if self.hotel else None,
            'user_id': self.user_id,
            'guest_id': self.guest_id,
            'guest_name': self.guest.full_name if self.guest else None,
            'check_in': self.check_in.isoformat() if self.check_in else None,
            'check_out': self.check_out.isoformat() if self.check_out else None,
            'adults': self.adults,
            'children': self.children,
            'total_amount': float(self.total_amount),
            'status': self.status,
            'special_requests': self.special_requests,
            'duration_nights': self.duration_nights,
            'can_cancel': self.can_cancel,
            'timezone': self.timezone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_rooms:
            data['rooms'] = [br.to_dict() for br in self.booking_rooms]
        
        if include_payments:
            data['payments'] = [p.to_dict() for p in self.payments]
        
        return data

class BookingRoom(db.Model):
    """BookingRoom model for many-to-many relationship between bookings and rooms"""
    __tablename__ = 'booking_rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    rate = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('rate >= 0', name='check_rate_positive'),
        db.UniqueConstraint('booking_id', 'room_id', name='unique_room_per_booking'),
    )
    
    def __repr__(self):
        return f'<BookingRoom {self.booking.booking_reference} - Room {self.room.room_number}>'
    
    def to_dict(self):
        """Convert booking room to dictionary"""
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'room_id': self.room_id,
            'room_number': self.room.room_number if self.room else None,
            'room_type': self.room.room_type.name if self.room and self.room.room_type else None,
            'rate': float(self.rate),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Event listeners for audit logging
@event.listens_for(Booking, 'after_insert')
def booking_after_insert(mapper, connection, target):
    """Log booking creation"""
    AuditLog.log_creation('bookings', target.id, target.to_dict(), target.user_id)

@event.listens_for(Booking, 'after_update')
def booking_after_update(mapper, connection, target):
    """Log booking updates"""
    AuditLog.log_update('bookings', target.id, target.to_dict(), target.user_id)

@event.listens_for(Guest, 'after_insert')
def guest_after_insert(mapper, connection, target):
    """Log guest creation"""
    AuditLog.log_creation('guests', target.id, target.to_dict(), None)

@event.listens_for(Guest, 'after_update')
def guest_after_update(mapper, connection, target):
    """Log guest updates"""
    AuditLog.log_update('guests', target.id, target.to_dict(), None)
