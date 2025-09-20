"""
Hotel, RoomType, and Room models
"""

from app import db
from datetime import datetime
from decimal import Decimal
import json
from sqlalchemy import event, CheckConstraint
from app.models.audit import AuditLog

class Hotel(db.Model):
    """Hotel model"""
    __tablename__ = 'hotels'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50))
    country = db.Column(db.String(50), nullable=False)
    postal_code = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    amenities = db.Column(db.JSON, default=list)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    room_types = db.relationship('RoomType', backref='hotel', lazy='dynamic', cascade='all, delete-orphan')
    rooms = db.relationship('Room', backref='hotel', lazy='dynamic', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='hotel', lazy='dynamic')
    
    def __repr__(self):
        return f'<Hotel {self.name}>'
    
    def to_dict(self):
        """Convert hotel to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'postal_code': self.postal_code,
            'phone': self.phone,
            'email': self.email,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'amenities': self.amenities,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class RoomType(db.Model):
    """Room type model"""
    __tablename__ = 'room_types'
    
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotels.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    max_occupancy = db.Column(db.Integer, nullable=False)
    amenities = db.Column(db.JSON, default=list)
    base_price = db.Column(db.Numeric(10, 2), nullable=False)
    pricing_rules = db.Column(db.JSON, default=dict)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    rooms = db.relationship('Room', backref='room_type', lazy='dynamic', cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('max_occupancy > 0', name='check_max_occupancy_positive'),
        CheckConstraint('base_price >= 0', name='check_base_price_positive'),
    )
    
    def __repr__(self):
        return f'<RoomType {self.name} at {self.hotel.name}>'
    
    def calculate_price(self, check_in, check_out, adults=1, children=0):
        """Calculate price for specific dates and occupancy"""
        # Base price calculation logic
        price = float(self.base_price)
        
        # Apply pricing rules if any
        if self.pricing_rules:
            # Weekend pricing
            if self.pricing_rules.get('weekend_multiplier'):
                # Simple weekend detection (Saturday = 5, Sunday = 6)
                from datetime import datetime
                check_in_date = datetime.strptime(check_in, '%Y-%m-%d') if isinstance(check_in, str) else check_in
                if check_in_date.weekday() in [5, 6]:  # Weekend
                    price *= self.pricing_rules['weekend_multiplier']
            
            # Season pricing
            if self.pricing_rules.get('season_multiplier'):
                month = check_in_date.month
                if month in [6, 7, 8]:  # Summer
                    price *= self.pricing_rules['season_multiplier']
        
        return Decimal(str(round(price, 2)))
    
    def to_dict(self):
        """Convert room type to dictionary"""
        return {
            'id': self.id,
            'hotel_id': self.hotel_id,
            'name': self.name,
            'description': self.description,
            'max_occupancy': self.max_occupancy,
            'amenities': self.amenities,
            'base_price': float(self.base_price),
            'pricing_rules': self.pricing_rules,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Room(db.Model):
    """Room model"""
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotels.id'), nullable=False)
    room_type_id = db.Column(db.Integer, db.ForeignKey('room_types.id'), nullable=False)
    room_number = db.Column(db.String(20), nullable=False)
    floor = db.Column(db.String(10))
    features = db.Column(db.JSON, default=dict)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    booking_rooms = db.relationship('BookingRoom', backref='room', lazy='dynamic')
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('hotel_id', 'room_number', name='unique_room_per_hotel'),
    )
    
    def __repr__(self):
        return f'<Room {self.room_number} at {self.hotel.name}>'
    
    def is_available(self, check_in, check_out):
        """Check if room is available for given dates"""
        from app.models.booking import Booking, BookingRoom
        
        # Convert string dates to datetime objects if needed
        if isinstance(check_in, str):
            check_in = datetime.strptime(check_in, '%Y-%m-%d')
        if isinstance(check_out, str):
            check_out = datetime.strptime(check_out, '%Y-%m-%d')
        
        # Check for overlapping bookings
        overlapping_bookings = db.session.query(BookingRoom).join(Booking).filter(
            BookingRoom.room_id == self.id,
            Booking.status.in_(['confirmed', 'checked_in']),
            db.or_(
                db.and_(
                    Booking.check_in < check_out,
                    Booking.check_out > check_in
                )
            )
        ).count()
        
        return overlapping_bookings == 0
    
    def to_dict(self):
        """Convert room to dictionary"""
        return {
            'id': self.id,
            'hotel_id': self.hotel_id,
            'room_type_id': self.room_type_id,
            'room_number': self.room_number,
            'floor': self.floor,
            'features': self.features,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Event listeners for audit logging
@event.listens_for(Hotel, 'after_insert')
def hotel_after_insert(mapper, connection, target):
    """Log hotel creation"""
    AuditLog.log_creation('hotels', target.id, target.to_dict(), None)

@event.listens_for(Hotel, 'after_update')
def hotel_after_update(mapper, connection, target):
    """Log hotel updates"""
    AuditLog.log_update('hotels', target.id, target.to_dict(), None)

@event.listens_for(RoomType, 'after_insert')
def room_type_after_insert(mapper, connection, target):
    """Log room type creation"""
    AuditLog.log_creation('room_types', target.id, target.to_dict(), None)

@event.listens_for(RoomType, 'after_update')
def room_type_after_update(mapper, connection, target):
    """Log room type updates"""
    AuditLog.log_update('room_types', target.id, target.to_dict(), None)
