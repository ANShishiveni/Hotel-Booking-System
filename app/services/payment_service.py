"""
Payment service for processing payments and handling webhooks
"""

from app import db
from app.models.payment import Payment
from app.models.booking import Booking
from app.models.audit import AuditLog
from datetime import datetime
from decimal import Decimal
import json
import hashlib
import hmac
import logging

logger = logging.getLogger(__name__)

class PaymentService:
    """Service class for handling payment operations"""
    
    def __init__(self):
        self.logger = logger
    
    def process_payment(self, booking_id, payment_method, amount, payment_data):
        """Process payment for a booking"""
        try:
            # Get booking
            booking = Booking.query.get(booking_id)
            if not booking:
                raise ValueError("Booking not found")
            
            # Validate amount
            if Decimal(str(amount)) != booking.total_amount:
                raise ValueError("Payment amount does not match booking total")
            
            # Create payment record
            payment = Payment(
                booking_id=booking_id,
                payment_method=payment_method,
                amount=amount,
                currency='USD',
                status='pending',
                payment_details=payment_data
            )
            
            db.session.add(payment)
            db.session.flush()  # Get payment ID
            
            # Process payment based on method
            if payment_method == 'stripe':
                self._process_stripe_payment(payment, payment_data)
            elif payment_method == 'paypal':
                self._process_paypal_payment(payment, payment_data)
            elif payment_method == 'bank_transfer':
                self._process_bank_transfer_payment(payment, payment_data)
            else:
                raise ValueError(f"Unsupported payment method: {payment_method}")
            
            # Update booking status if payment successful
            if payment.status == 'completed':
                booking.status = 'confirmed'
            
            db.session.commit()
            
            # Log payment creation
            AuditLog.log_custom_action(
                'payments', payment.id, 'PAYMENT_CREATED',
                {
                    'payment_method': payment_method,
                    'amount': float(amount),
                    'status': payment.status
                },
                booking.user_id
            )
            
            return payment
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error processing payment: {str(e)}")
            raise
    
    def _process_stripe_payment(self, payment, payment_data):
        """Process Stripe payment (mock implementation)"""
        try:
            # Mock Stripe payment processing
            # In real implementation, use Stripe API
            
            # Simulate payment processing delay
            import time
            time.sleep(0.1)
            
            # Mock successful payment
            payment.transaction_id = f"stripe_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{payment.id}"
            payment.status = 'completed'
            payment.processed_at = datetime.utcnow()
            
            # Store Stripe-specific details
            payment.payment_details.update({
                'stripe_payment_intent_id': payment.transaction_id,
                'payment_method_id': payment_data.get('payment_method_id'),
                'receipt_url': f"https://pay.stripe.com/receipts/{payment.transaction_id}",
                'payment_method_type': payment_data.get('payment_method_type', 'card'),
                'card_last4': payment_data.get('card_last4'),
                'card_brand': payment_data.get('card_brand')
            })
            
            self.logger.info(f"Stripe payment processed: {payment.transaction_id}")
            
        except Exception as e:
            payment.status = 'failed'
            payment.failure_reason = f"Stripe payment failed: {str(e)}"
            self.logger.error(f"Stripe payment error: {str(e)}")
            raise
    
    def _process_paypal_payment(self, payment, payment_data):
        """Process PayPal payment (mock implementation)"""
        try:
            # Mock PayPal payment processing
            # In real implementation, use PayPal API
            
            # Simulate payment processing delay
            import time
            time.sleep(0.1)
            
            # Mock successful payment
            payment.transaction_id = f"paypal_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{payment.id}"
            payment.status = 'completed'
            payment.processed_at = datetime.utcnow()
            
            # Store PayPal-specific details
            payment.payment_details.update({
                'paypal_transaction_id': payment.transaction_id,
                'payer_id': payment_data.get('payer_id'),
                'payer_email': payment_data.get('payer_email'),
                'order_id': payment_data.get('order_id')
            })
            
            self.logger.info(f"PayPal payment processed: {payment.transaction_id}")
            
        except Exception as e:
            payment.status = 'failed'
            payment.failure_reason = f"PayPal payment failed: {str(e)}"
            self.logger.error(f"PayPal payment error: {str(e)}")
            raise
    
    def _process_bank_transfer_payment(self, payment, payment_data):
        """Process bank transfer payment"""
        try:
            # Bank transfer is always pending until manually confirmed
            payment.status = 'pending'
            payment.transaction_id = f"bank_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{payment.id}"
            
            # Store bank transfer details
            payment.payment_details.update({
                'bank_name': payment_data.get('bank_name'),
                'account_number': payment_data.get('account_number'),
                'routing_number': payment_data.get('routing_number'),
                'reference_number': payment.transaction_id
            })
            
            self.logger.info(f"Bank transfer payment created: {payment.transaction_id}")
            
        except Exception as e:
            payment.status = 'failed'
            payment.failure_reason = f"Bank transfer payment failed: {str(e)}"
            self.logger.error(f"Bank transfer payment error: {str(e)}")
            raise
    
    def process_refund(self, payment_id, amount=None, reason=None):
        """Process refund for a payment"""
        try:
            with db.session.begin_nested():
                # Lock payment for update
                payment = db.session.query(Payment).with_for_update().filter_by(
                    id=payment_id
                ).first()
                
                if not payment:
                    raise ValueError("Payment not found")
                
                if not payment.is_refundable:
                    raise ValueError("Payment cannot be refunded")
                
                refund_amount = amount or payment.amount
                
                if refund_amount > payment.amount:
                    raise ValueError("Refund amount cannot exceed original payment")
                
                # Process refund based on payment method
                if payment.payment_method == 'stripe':
                    self._process_stripe_refund(payment, refund_amount, reason)
                elif payment.payment_method == 'paypal':
                    self._process_paypal_refund(payment, refund_amount, reason)
                else:
                    # For bank transfers and other methods, mark as refunded
                    payment.status = 'refunded'
                
                # Store refund details
                payment.payment_details['refund'] = {
                    'amount': float(refund_amount),
                    'reason': reason,
                    'refunded_at': datetime.utcnow().isoformat(),
                    'refund_method': payment.payment_method
                }
                
                db.session.commit()
                
                # Log refund
                AuditLog.log_custom_action(
                    'payments', payment.id, 'PAYMENT_REFUNDED',
                    {
                        'refund_amount': float(refund_amount),
                        'reason': reason
                    },
                    None  # Admin action
                )
                
                return payment
                
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error processing refund: {str(e)}")
            raise
    
    def _process_stripe_refund(self, payment, amount, reason):
        """Process Stripe refund (mock implementation)"""
        try:
            # Mock Stripe refund processing
            # In real implementation, use Stripe API
            
            refund_id = f"stripe_refund_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            payment.status = 'refunded'
            payment.payment_details['refund']['stripe_refund_id'] = refund_id
            
            self.logger.info(f"Stripe refund processed: {refund_id}")
            
        except Exception as e:
            self.logger.error(f"Stripe refund error: {str(e)}")
            raise
    
    def _process_paypal_refund(self, payment, amount, reason):
        """Process PayPal refund (mock implementation)"""
        try:
            # Mock PayPal refund processing
            # In real implementation, use PayPal API
            
            refund_id = f"paypal_refund_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            payment.status = 'refunded'
            payment.payment_details['refund']['paypal_refund_id'] = refund_id
            
            self.logger.info(f"PayPal refund processed: {refund_id}")
            
        except Exception as e:
            self.logger.error(f"PayPal refund error: {str(e)}")
            raise
    
    def verify_stripe_signature(self, payload, signature, secret):
        """Verify Stripe webhook signature"""
        try:
            # Extract timestamp and signature from header
            timestamp, signature_hash = signature.split(',')
            timestamp = timestamp.split('=')[1]
            signature_hash = signature_hash.split('=')[1]
            
            # Create expected signature
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                f"{timestamp}.{payload.decode('utf-8')}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature_hash, expected_signature)
            
        except Exception as e:
            self.logger.error(f"Error verifying Stripe signature: {str(e)}")
            return False
    
    def handle_payment_success(self, payment_intent_data):
        """Handle successful payment webhook from Stripe"""
        try:
            # Find payment by transaction ID
            transaction_id = payment_intent_data.get('id')
            payment = Payment.query.filter_by(transaction_id=transaction_id).first()
            
            if not payment:
                self.logger.warning(f"Payment not found for transaction: {transaction_id}")
                return
            
            # Update payment status
            payment.status = 'completed'
            payment.processed_at = datetime.utcnow()
            
            # Update booking status
            booking = payment.booking
            if booking and booking.status == 'pending':
                booking.status = 'confirmed'
            
            db.session.commit()
            
            # Log webhook handling
            AuditLog.log_custom_action(
                'payments', payment.id, 'WEBHOOK_PAYMENT_SUCCESS',
                {'transaction_id': transaction_id},
                None
            )
            
            self.logger.info(f"Payment success webhook handled: {transaction_id}")
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error handling payment success webhook: {str(e)}")
            raise
    
    def handle_payment_failure(self, payment_intent_data):
        """Handle failed payment webhook from Stripe"""
        try:
            # Find payment by transaction ID
            transaction_id = payment_intent_data.get('id')
            payment = Payment.query.filter_by(transaction_id=transaction_id).first()
            
            if not payment:
                self.logger.warning(f"Payment not found for transaction: {transaction_id}")
                return
            
            # Update payment status
            payment.status = 'failed'
            payment.failure_reason = payment_intent_data.get('last_payment_error', {}).get('message', 'Payment failed')
            
            db.session.commit()
            
            # Log webhook handling
            AuditLog.log_custom_action(
                'payments', payment.id, 'WEBHOOK_PAYMENT_FAILURE',
                {'transaction_id': transaction_id, 'reason': payment.failure_reason},
                None
            )
            
            self.logger.info(f"Payment failure webhook handled: {transaction_id}")
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error handling payment failure webhook: {str(e)}")
            raise
    
    def handle_dispute_created(self, dispute_data):
        """Handle dispute created webhook from Stripe"""
        try:
            # Find payment by charge ID
            charge_id = dispute_data.get('charge')
            payment = Payment.query.filter_by(transaction_id=charge_id).first()
            
            if not payment:
                self.logger.warning(f"Payment not found for charge: {charge_id}")
                return
            
            # Store dispute information
            payment.payment_details['dispute'] = {
                'dispute_id': dispute_data.get('id'),
                'reason': dispute_data.get('reason'),
                'status': dispute_data.get('status'),
                'amount': dispute_data.get('amount'),
                'created_at': dispute_data.get('created')
            }
            
            db.session.commit()
            
            # Log dispute
            AuditLog.log_custom_action(
                'payments', payment.id, 'WEBHOOK_DISPUTE_CREATED',
                {
                    'dispute_id': dispute_data.get('id'),
                    'reason': dispute_data.get('reason'),
                    'amount': dispute_data.get('amount')
                },
                None
            )
            
            self.logger.info(f"Dispute created webhook handled: {dispute_data.get('id')}")
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error handling dispute created webhook: {str(e)}")
            raise
    
    def handle_paypal_payment_success(self, payment_data):
        """Handle successful payment webhook from PayPal"""
        try:
            # Find payment by transaction ID
            transaction_id = payment_data.get('id')
            payment = Payment.query.filter_by(transaction_id=transaction_id).first()
            
            if not payment:
                self.logger.warning(f"Payment not found for transaction: {transaction_id}")
                return
            
            # Update payment status
            payment.status = 'completed'
            payment.processed_at = datetime.utcnow()
            
            # Update booking status
            booking = payment.booking
            if booking and booking.status == 'pending':
                booking.status = 'confirmed'
            
            db.session.commit()
            
            # Log webhook handling
            AuditLog.log_custom_action(
                'payments', payment.id, 'WEBHOOK_PAYPAL_PAYMENT_SUCCESS',
                {'transaction_id': transaction_id},
                None
            )
            
            self.logger.info(f"PayPal payment success webhook handled: {transaction_id}")
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error handling PayPal payment success webhook: {str(e)}")
            raise
    
    def handle_paypal_payment_failure(self, payment_data):
        """Handle failed payment webhook from PayPal"""
        try:
            # Find payment by transaction ID
            transaction_id = payment_data.get('id')
            payment = Payment.query.filter_by(transaction_id=transaction_id).first()
            
            if not payment:
                self.logger.warning(f"Payment not found for transaction: {transaction_id}")
                return
            
            # Update payment status
            payment.status = 'failed'
            payment.failure_reason = payment_data.get('reason_code', 'Payment failed')
            
            db.session.commit()
            
            # Log webhook handling
            AuditLog.log_custom_action(
                'payments', payment.id, 'WEBHOOK_PAYPAL_PAYMENT_FAILURE',
                {'transaction_id': transaction_id, 'reason': payment.failure_reason},
                None
            )
            
            self.logger.info(f"PayPal payment failure webhook handled: {transaction_id}")
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error handling PayPal payment failure webhook: {str(e)}")
            raise
