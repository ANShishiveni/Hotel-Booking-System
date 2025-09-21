from app import db, jwt
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
import pytz

# Association table for many-to-many relationship between users and roles
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class Role(db.Model):
    """User roles for authorization"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    permissions = db.Column(db.JSON)  # Store permissions as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Role {self.name}>'

class User(db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    roles = db.relationship('Role', secondary=user_roles, backref='users')
    bookings = db.relationship('Booking', backref='user', lazy='dynamic')
    reviews = db.relationship('Review', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role_name):
        """Check if user has specific role"""
        return any(role.name == role_name for role in self.roles)
    
    def get_permissions(self):
        """Get all permissions for user"""
        permissions = set()
        for role in self.roles:
            if role.permissions:
                permissions.update(role.permissions)
        return list(permissions)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'roles': [role.name for role in self.roles]
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class Hotel(db.Model):
    """Hotel model"""
    __tablename__ = 'hotels'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(500), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100))
    country = db.Column(db.String(100), nullable=False, default='Namibia')
    postal_code = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    website = db.Column(db.String(200))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    star_rating = db.Column(db.Integer, CheckConstraint('star_rating >= 1 AND star_rating <= 5'))
    amenities = db.Column(db.JSON)  # Store amenities as JSON array
    images = db.Column(db.JSON)  # Store image URLs as JSON array
    policies = db.Column(db.JSON)  # Store hotel policies as JSON
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    room_types = db.relationship('RoomType', backref='hotel', lazy='dynamic', cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='hotel', lazy='dynamic')
    
    # Indexes
    __table_args__ = (
        Index('idx_hotel_city', 'city'),
        Index('idx_hotel_country', 'country'),
        Index('idx_hotel_star_rating', 'star_rating'),
    )
    
    def to_dict(self):
        """Convert hotel to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'postal_code': self.postal_code,
            'phone': self.phone,
            'email': self.email,
            'website': self.website,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'star_rating': self.star_rating,
            'amenities': self.amenities or [],
            'images': self.images or [],
            'policies': self.policies or {},
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'room_types_count': self.room_types.count(),
            'average_rating': self.get_average_rating()
        }
    
    def get_average_rating(self):
        """Calculate average rating from reviews"""
        reviews = self.reviews.filter(Review.is_active == True).all()
        if not reviews:
            return 0
        return sum(review.rating for review in reviews) / len(reviews)
    
    def __repr__(self):
        return f'<Hotel {self.name}>'

class RoomType(db.Model):
    """Room type model (e.g., Standard, Deluxe, Suite)"""
    __tablename__ = 'room_types'
    
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotels.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    base_price = db.Column(db.Numeric(10, 2), nullable=False)
    max_occupancy = db.Column(db.Integer, nullable=False)
    bed_type = db.Column(db.String(50))
    room_size = db.Column(db.Integer)  # Size in square meters
    amenities = db.Column(db.JSON)  # Room-specific amenities
    images = db.Column(db.JSON)  # Room images
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    rooms = db.relationship('Room', backref='room_type', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert room type to dictionary"""
        return {
            'id': self.id,
            'hotel_id': self.hotel_id,
            'name': self.name,
            'description': self.description,
            'base_price': float(self.base_price),
            'max_occupancy': self.max_occupancy,
            'bed_type': self.bed_type,
            'room_size': self.room_size,
            'amenities': self.amenities or [],
            'images': self.images or [],
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'available_rooms': self.get_available_rooms_count()
        }
    
    def get_available_rooms_count(self):
        """Get count of available rooms for this type"""
        return self.rooms.filter(Room.is_active == True).count()
    
    def __repr__(self):
        return f'<RoomType {self.name} at {self.hotel.name}>'

class Room(db.Model):
    """Individual room model"""
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotels.id'), nullable=False)
    room_type_id = db.Column(db.Integer, db.ForeignKey('room_types.id'), nullable=False)
    room_number = db.Column(db.String(20), nullable=False)
    floor = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='room', lazy='dynamic')
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('hotel_id', 'room_number', name='unique_room_per_hotel'),
        Index('idx_room_hotel_type', 'hotel_id', 'room_type_id'),
    )
    
    def to_dict(self):
        """Convert room to dictionary"""
        return {
            'id': self.id,
            'hotel_id': self.hotel_id,
            'room_type_id': self.room_type_id,
            'room_number': self.room_number,
            'floor': self.floor,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Room {self.room_number} at {self.hotel.name}>'

class Booking(db.Model):
    """Booking model"""
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_reference = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotels.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    room_type_id = db.Column(db.Integer, db.ForeignKey('room_types.id'), nullable=False)
    
    # Booking dates and details
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    nights = db.Column(db.Integer, nullable=False)
    adults = db.Column(db.Integer, nullable=False, default=1)
    children = db.Column(db.Integer, default=0)
    
    # Pricing
    room_rate = db.Column(db.Numeric(10, 2), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    
    # Status and metadata
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, confirmed, cancelled, checked_in, checked_out
    special_requests = db.Column(db.Text)
    guest_notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    
    # Relationships
    guests = db.relationship('Guest', backref='booking', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='booking', lazy='dynamic', cascade='all, delete-orphan')
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint('check_out_date > check_in_date', name='valid_dates'),
        CheckConstraint('nights > 0', name='positive_nights'),
        CheckConstraint('adults > 0', name='positive_adults'),
        CheckConstraint('children >= 0', name='non_negative_children'),
        CheckConstraint("status IN ('pending', 'confirmed', 'cancelled', 'checked_in', 'checked_out')", name='valid_status'),
        Index('idx_booking_dates', 'check_in_date', 'check_out_date'),
        Index('idx_booking_status', 'status'),
        Index('idx_booking_user', 'user_id'),
        Index('idx_booking_hotel', 'hotel_id'),
        Index('idx_booking_room', 'room_id'),
    )
    
    def generate_booking_reference(self):
        """Generate unique booking reference"""
        import random
        import string
        
        while True:
            ref = 'BK' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Booking.query.filter_by(booking_reference=ref).first():
                return ref
    
    def to_dict(self):
        """Convert booking to dictionary"""
        return {
            'id': self.id,
            'booking_reference': self.booking_reference,
            'user_id': self.user_id,
            'hotel_id': self.hotel_id,
            'room_id': self.room_id,
            'room_type_id': self.room_type_id,
            'check_in_date': self.check_in_date.isoformat(),
            'check_out_date': self.check_out_date.isoformat(),
            'nights': self.nights,
            'adults': self.adults,
            'children': self.children,
            'room_rate': float(self.room_rate),
            'total_amount': float(self.total_amount),
            'tax_amount': float(self.tax_amount),
            'discount_amount': float(self.discount_amount),
            'status': self.status,
            'special_requests': self.special_requests,
            'guest_notes': self.guest_notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'hotel': self.hotel.to_dict() if self.hotel else None,
            'room': self.room.to_dict() if self.room else None,
            'room_type': self.room_type.to_dict() if self.room_type else None,
            'guests': [guest.to_dict() for guest in self.guests],
            'payments': [payment.to_dict() for payment in self.payments]
        }
    
    def __repr__(self):
        return f'<Booking {self.booking_reference}>'

class Guest(db.Model):
    """Guest information for bookings"""
    __tablename__ = 'guests'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    nationality = db.Column(db.String(100))
    id_number = db.Column(db.String(50))
    passport_number = db.Column(db.String(50))
    is_primary_guest = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert guest to dictionary"""
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'nationality': self.nationality,
            'id_number': self.id_number,
            'passport_number': self.passport_number,
            'is_primary_guest': self.is_primary_guest,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Guest {self.first_name} {self.last_name}>'

class Payment(db.Model):
    """Payment model"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    payment_reference = db.Column(db.String(50), unique=True, nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='NAD')
    payment_method = db.Column(db.String(50), nullable=False)  # card, cash, bank_transfer, etc.
    payment_provider = db.Column(db.String(50))  # stripe, paypal, etc.
    provider_transaction_id = db.Column(db.String(100))
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, completed, failed, refunded
    payment_intent_id = db.Column(db.String(100))  # For Stripe integration
    metadata = db.Column(db.JSON)  # Store provider-specific data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint('amount > 0', name='positive_amount'),
        CheckConstraint("status IN ('pending', 'completed', 'failed', 'refunded')", name='valid_payment_status'),
        Index('idx_payment_booking', 'booking_id'),
        Index('idx_payment_status', 'status'),
        Index('idx_payment_provider', 'payment_provider'),
    )
    
    def generate_payment_reference(self):
        """Generate unique payment reference"""
        import random
        import string
        
        while True:
            ref = 'PAY' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            if not Payment.query.filter_by(payment_reference=ref).first():
                return ref
    
    def to_dict(self):
        """Convert payment to dictionary"""
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'payment_reference': self.payment_reference,
            'amount': float(self.amount),
            'currency': self.currency,
            'payment_method': self.payment_method,
            'payment_provider': self.payment_provider,
            'provider_transaction_id': self.provider_transaction_id,
            'status': self.status,
            'payment_intent_id': self.payment_intent_id,
            'metadata': self.metadata or {},
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
    
    def __repr__(self):
        return f'<Payment {self.payment_reference}>'

class Review(db.Model):
    """Hotel review model"""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotels.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200))
    comment = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='valid_rating'),
        db.UniqueConstraint('hotel_id', 'user_id', 'booking_id', name='unique_review_per_booking'),
        Index('idx_review_hotel', 'hotel_id'),
        Index('idx_review_user', 'user_id'),
        Index('idx_review_rating', 'rating'),
    )
    
    def to_dict(self):
        """Convert review to dictionary"""
        return {
            'id': self.id,
            'hotel_id': self.hotel_id,
            'user_id': self.user_id,
            'booking_id': self.booking_id,
            'rating': self.rating,
            'title': self.title,
            'comment': self.comment,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'user': {
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'username': self.user.username
            } if self.user else None
        }
    
    def __repr__(self):
        return f'<Review {self.rating}/5 for {self.hotel.name}>'

class AuditLog(db.Model):
    """Audit log for tracking changes"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(20), nullable=False)  # CREATE, UPDATE, DELETE
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint("action IN ('CREATE', 'UPDATE', 'DELETE')", name='valid_action'),
        Index('idx_audit_table_record', 'table_name', 'record_id'),
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_created', 'created_at'),
    )
    
    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            'id': self.id,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'action': self.action,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<AuditLog {self.action} {self.table_name}.{self.record_id}>'

# JWT token blacklist for logout functionality
class TokenBlacklist(db.Model):
    """Blacklisted JWT tokens"""
    __tablename__ = 'token_blacklist'
    
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), unique=True, nullable=False, index=True)
    token_type = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    revoked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TokenBlacklist {self.jti}>'

# JWT callbacks
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    """Check if token is blacklisted"""
    jti = jwt_payload['jti']
    token = TokenBlacklist.query.filter_by(jti=jti).first()
    return token is not None

@jwt.user_identity_loader
def user_identity_lookup(user):
    """Return user identity for JWT"""
    return user.id

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    """Load user from JWT data"""
    identity = jwt_data['sub']
    return User.query.filter_by(id=identity).one_or_none()
