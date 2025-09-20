"""
Payment model for handling payment transactions
"""

from app import db
from datetime import datetime
from decimal import Decimal
import json
import hashlib
import hmac
from sqlalchemy import event, CheckConstraint
from app.models.audit import AuditLog

class Payment(db.Model):
    """Payment model"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # stripe, paypal, cash, etc.
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    status = db.Column(db.String(20), nullable=False, default='pending')
    transaction_id = db.Column(db.String(100), unique=True, index=True)
    payment_details = db.Column(db.JSON, default=dict)
    webhook_signature = db.Column(db.Text)
    failure_reason = db.Column(db.Text)
    processed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('amount > 0', name='check_amount_positive'),
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed', 'refunded', 'cancelled')", name='check_valid_payment_status'),
        CheckConstraint("payment_method IN ('stripe', 'paypal', 'cash', 'bank_transfer')", name='check_valid_payment_method'),
    )
    
    def __repr__(self):
        return f'<Payment {self.transaction_id} - {self.status}>'
    
    @property
    def is_successful(self):
        """Check if payment is successful"""
        return self.status == 'completed'
    
    @property
    def is_refundable(self):
        """Check if payment can be refunded"""
        return self.status == 'completed' and self.booking.status in ['confirmed', 'checked_in', 'checked_out']
    
    def process_payment(self, payment_data=None):
        """Process payment (mock implementation)"""
        try:
            self.status = 'processing'
            db.session.commit()
            
            # Mock payment processing logic
            # In real implementation, this would integrate with payment gateway
            if self.payment_method == 'stripe':
                self._process_stripe_payment(payment_data)
            elif self.payment_method == 'paypal':
                self._process_paypal_payment(payment_data)
            else:
                # For demo purposes, mark as completed
                self.status = 'completed'
                self.processed_at = datetime.utcnow()
            
            db.session.commit()
            return True
            
        except Exception as e:
            self.status = 'failed'
            self.failure_reason = str(e)
            db.session.commit()
            return False
    
    def _process_stripe_payment(self, payment_data):
        """Process Stripe payment (mock)"""
        # Mock Stripe payment processing
        # In real implementation, use Stripe API
        self.transaction_id = f"stripe_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{self.id}"
        self.status = 'completed'
        self.processed_at = datetime.utcnow()
        
        # Store payment details
        self.payment_details.update({
            'stripe_payment_intent_id': self.transaction_id,
            'payment_method_id': payment_data.get('payment_method_id') if payment_data else None,
            'receipt_url': f"https://pay.stripe.com/receipts/{self.transaction_id}"
        })
    
    def _process_paypal_payment(self, payment_data):
        """Process PayPal payment (mock)"""
        # Mock PayPal payment processing
        self.transaction_id = f"paypal_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{self.id}"
        self.status = 'completed'
        self.processed_at = datetime.utcnow()
        
        # Store payment details
        self.payment_details.update({
            'paypal_transaction_id': self.transaction_id,
            'payer_id': payment_data.get('payer_id') if payment_data else None
        })
    
    def refund_payment(self, amount=None, reason=None):
        """Refund payment"""
        if not self.is_refundable:
            raise ValueError("Payment cannot be refunded")
        
        refund_amount = amount or self.amount
        
        try:
            # Mock refund processing
            # In real implementation, call payment gateway refund API
            self.status = 'refunded'
            self.payment_details['refund'] = {
                'amount': float(refund_amount),
                'reason': reason,
                'refunded_at': datetime.utcnow().isoformat()
            }
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def verify_webhook_signature(self, payload, signature, secret):
        """Verify webhook signature (for Stripe)"""
        if not signature or not secret:
            return False
        
        try:
            # Stripe webhook signature verification
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(f"sha256={expected_signature}", signature)
        except Exception:
            return False
    
    def to_dict(self, include_sensitive=False):
        """Convert payment to dictionary"""
        data = {
            'id': self.id,
            'booking_id': self.booking_id,
            'booking_reference': self.booking.booking_reference if self.booking else None,
            'payment_method': self.payment_method,
            'amount': float(self.amount),
            'currency': self.currency,
            'status': self.status,
            'transaction_id': self.transaction_id,
            'is_successful': self.is_successful,
            'is_refundable': self.is_refundable,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            data['payment_details'] = self.payment_details
            data['failure_reason'] = self.failure_reason
        
        return data

# Event listeners for audit logging
@event.listens_for(Payment, 'after_insert')
def payment_after_insert(mapper, connection, target):
    """Log payment creation"""
    AuditLog.log_creation('payments', target.id, target.to_dict(include_sensitive=True), target.booking.user_id if target.booking else None)

@event.listens_for(Payment, 'after_update')
def payment_after_update(mapper, connection, target):
    """Log payment updates"""
    AuditLog.log_update('payments', target.id, target.to_dict(include_sensitive=True), target.booking.user_id if target.booking else None)
