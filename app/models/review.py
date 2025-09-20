"""
Review model for guest reviews and ratings
"""

from app import db
from datetime import datetime
from sqlalchemy import event, CheckConstraint
from app.models.audit import AuditLog

class Review(db.Model):
    """Review model for hotel reviews"""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200))
    comment = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
        db.UniqueConstraint('booking_id', 'user_id', name='unique_review_per_booking_user'),
    )
    
    def __repr__(self):
        return f'<Review {self.rating}/5 by {self.user.email}>'
    
    @property
    def rating_stars(self):
        """Get rating as star representation"""
        return '★' * self.rating + '☆' * (5 - self.rating)
    
    @property
    def can_be_edited(self):
        """Check if review can be edited (within 24 hours of creation)"""
        return (datetime.utcnow() - self.created_at).total_seconds() < 86400  # 24 hours
    
    def to_dict(self, include_booking_details=False):
        """Convert review to dictionary"""
        data = {
            'id': self.id,
            'booking_id': self.booking_id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'rating': self.rating,
            'rating_stars': self.rating_stars,
            'title': self.title,
            'comment': self.comment,
            'is_verified': self.is_verified,
            'can_be_edited': self.can_be_edited,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_booking_details:
            data['booking'] = {
                'reference': self.booking.booking_reference if self.booking else None,
                'hotel_name': self.booking.hotel.name if self.booking and self.booking.hotel else None,
                'check_in': self.booking.check_in.isoformat() if self.booking and self.booking.check_in else None,
                'check_out': self.booking.check_out.isoformat() if self.booking and self.booking.check_out else None
            }
        
        return data

# Event listeners for audit logging
@event.listens_for(Review, 'after_insert')
def review_after_insert(mapper, connection, target):
    """Log review creation"""
    AuditLog.log_creation('reviews', target.id, target.to_dict(), target.user_id)

@event.listens_for(Review, 'after_update')
def review_after_update(mapper, connection, target):
    """Log review updates"""
    AuditLog.log_update('reviews', target.id, target.to_dict(), target.user_id)
