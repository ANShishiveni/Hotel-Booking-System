"""
Payment routes for processing payments and handling webhooks
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, limiter
from app.models.user import User
from app.models.booking import Booking
from app.models.payment import Payment
from app.services.payment_service import PaymentService
from app.utils.decorators import validate_json, require_permissions
from datetime import datetime
import json
import hashlib
import hmac

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/process', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
@validate_json(['booking_id', 'payment_method', 'payment_data'])
def process_payment():
    """Process payment for a booking"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get booking
        booking = Booking.query.get_or_404(data['booking_id'])
        
        # Check if user owns this booking
        if booking.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if booking can be paid for
        if booking.status not in ['pending', 'confirmed']:
            return jsonify({'error': 'Booking cannot be paid for'}), 400
        
        # Check if payment already exists and is successful
        existing_payment = Payment.query.filter_by(
            booking_id=booking.id,
            status='completed'
        ).first()
        
        if existing_payment:
            return jsonify({'error': 'Booking already paid'}), 400
        
        # Use payment service to process payment
        payment_service = PaymentService()
        payment = payment_service.process_payment(
            booking_id=booking.id,
            payment_method=data['payment_method'],
            amount=float(booking.total_amount),
            payment_data=data['payment_data']
        )
        
        return jsonify({
            'message': 'Payment processed successfully',
            'payment': payment.to_dict(include_sensitive=True)
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Payment processing error: {str(e)}")
        return jsonify({'error': 'Payment processing failed'}), 500

@payments_bp.route('/<int:payment_id>', methods=['GET'])
@jwt_required()
def get_payment(payment_id):
    """Get payment details"""
    try:
        current_user_id = get_jwt_identity()
        
        payment = Payment.query.get_or_404(payment_id)
        
        # Check if user owns this payment or is admin
        if payment.booking.user_id != current_user_id and not _is_admin(current_user_id):
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({
            'payment': payment.to_dict(include_sensitive=True)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get payment error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve payment'}), 500

@payments_bp.route('/<int:payment_id>/refund', methods=['POST'])
@jwt_required()
@require_permissions(['admin_all'])
@validate_json(['amount', 'reason'])
def refund_payment(payment_id):
    """Refund a payment (admin only)"""
    try:
        payment = Payment.query.get_or_404(payment_id)
        
        if not payment.is_refundable:
            return jsonify({'error': 'Payment cannot be refunded'}), 400
        
        refund_amount = request.get_json().get('amount')
        refund_reason = request.get_json().get('reason')
        
        # Use payment service to process refund
        payment_service = PaymentService()
        payment_service.process_refund(
            payment_id=payment_id,
            amount=refund_amount,
            reason=refund_reason
        )
        
        return jsonify({
            'message': 'Refund processed successfully',
            'payment': payment.to_dict(include_sensitive=True)
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Refund error: {str(e)}")
        return jsonify({'error': 'Refund processing failed'}), 500

@payments_bp.route('/webhook/stripe', methods=['POST'])
@limiter.limit("100 per minute")
def stripe_webhook():
    """Handle Stripe webhook events"""
    try:
        # Get webhook signature
        signature = request.headers.get('Stripe-Signature')
        if not signature:
            return jsonify({'error': 'Missing signature'}), 400
        
        # Get webhook secret from config
        webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
        if not webhook_secret:
            return jsonify({'error': 'Webhook secret not configured'}), 500
        
        # Get raw payload
        payload = request.get_data()
        
        # Verify signature
        payment_service = PaymentService()
        if not payment_service.verify_stripe_signature(payload, signature, webhook_secret):
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Parse event
        event = json.loads(payload.decode('utf-8'))
        
        # Handle different event types
        if event['type'] == 'payment_intent.succeeded':
            payment_service.handle_payment_success(event['data']['object'])
        elif event['type'] == 'payment_intent.payment_failed':
            payment_service.handle_payment_failure(event['data']['object'])
        elif event['type'] == 'charge.dispute.created':
            payment_service.handle_dispute_created(event['data']['object'])
        
        return jsonify({'status': 'success'}), 200
        
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON payload'}), 400
    except Exception as e:
        current_app.logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': 'Webhook processing failed'}), 500

@payments_bp.route('/webhook/paypal', methods=['POST'])
@limiter.limit("100 per minute")
def paypal_webhook():
    """Handle PayPal webhook events"""
    try:
        # Get webhook signature
        signature = request.headers.get('PAYPAL-TRANSMISSION-SIG')
        if not signature:
            return jsonify({'error': 'Missing signature'}), 400
        
        # Get raw payload
        payload = request.get_data()
        
        # Parse event
        event = json.loads(payload.decode('utf-8'))
        
        # Handle different event types
        payment_service = PaymentService()
        if event['event_type'] == 'PAYMENT.CAPTURE.COMPLETED':
            payment_service.handle_paypal_payment_success(event['resource'])
        elif event['event_type'] == 'PAYMENT.CAPTURE.DENIED':
            payment_service.handle_paypal_payment_failure(event['resource'])
        
        return jsonify({'status': 'success'}), 200
        
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON payload'}), 400
    except Exception as e:
        current_app.logger.error(f"PayPal webhook error: {str(e)}")
        return jsonify({'error': 'PayPal webhook processing failed'}), 500

@payments_bp.route('/booking/<int:booking_id>', methods=['GET'])
@jwt_required()
def get_booking_payments(booking_id):
    """Get all payments for a booking"""
    try:
        current_user_id = get_jwt_identity()
        
        booking = Booking.query.get_or_404(booking_id)
        
        # Check if user owns this booking or is admin
        if booking.user_id != current_user_id and not _is_admin(current_user_id):
            return jsonify({'error': 'Access denied'}), 403
        
        payments = Payment.query.filter_by(booking_id=booking_id).all()
        
        return jsonify({
            'payments': [payment.to_dict(include_sensitive=True) for payment in payments]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get booking payments error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve payments'}), 500

@payments_bp.route('/methods', methods=['GET'])
@limiter.limit("30 per minute")
def get_payment_methods():
    """Get available payment methods"""
    try:
        payment_methods = [
            {
                'id': 'stripe',
                'name': 'Credit Card',
                'description': 'Pay with Visa, MasterCard, American Express',
                'icon': 'credit-card',
                'enabled': bool(current_app.config.get('STRIPE_SECRET_KEY'))
            },
            {
                'id': 'paypal',
                'name': 'PayPal',
                'description': 'Pay with PayPal account',
                'icon': 'paypal',
                'enabled': bool(current_app.config.get('PAYPAL_CLIENT_ID'))
            },
            {
                'id': 'bank_transfer',
                'name': 'Bank Transfer',
                'description': 'Direct bank transfer',
                'icon': 'university',
                'enabled': True
            }
        ]
        
        # Filter enabled payment methods
        enabled_methods = [method for method in payment_methods if method['enabled']]
        
        return jsonify({
            'payment_methods': enabled_methods
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get payment methods error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve payment methods'}), 500

def _is_admin(user_id):
    """Check if user is admin"""
    user = User.query.get(user_id)
    return user and user.is_admin()
