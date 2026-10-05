from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Booking, Payment, AuditLog
from app import db
from datetime import datetime
import stripe
import os
import hmac
import hashlib

payments_bp = Blueprint('payments', __name__)

# Configure Stripe from the environment. Never fall back to a shared/demo secret.
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

@payments_bp.route('/create-payment-intent', methods=['POST'])
@jwt_required()
def create_payment_intent():
    """Create a Stripe payment intent for a booking"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data or not data.get('booking_id'):
            return jsonify({'error': 'booking_id is required'}), 400
        
        booking = Booking.query.filter_by(
            id=data['booking_id'], 
            user_id=current_user_id
        ).first()
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        if booking.status not in ['pending', 'confirmed']:
            return jsonify({'error': 'Booking cannot be paid for'}), 400
        
        # Check if payment already exists
        existing_payment = Payment.query.filter_by(
            booking_id=booking.id,
            status='completed'
        ).first()
        
        if existing_payment:
            return jsonify({'error': 'Booking already paid'}), 400
        
        # Create payment record
        try:
            payment = Payment(
                booking_id=booking.id,
                payment_reference=Payment().generate_payment_reference(),
                amount=booking.total_amount,
                currency='NAD',
                payment_method='card',
                payment_provider='stripe',
                status='pending'
            )
        except Exception as e:
            current_app.logger.error(f"Error creating payment record: {str(e)}")
            return jsonify({'error': 'Failed to create payment record'}), 500
        
        db.session.add(payment)
        db.session.flush()  # Get payment ID
        
        # Create Stripe payment intent (mock)
        try:
            # In a real implementation, you would use:
            # intent = stripe.PaymentIntent.create(
            #     amount=int(booking.total_amount * 100),  # Convert to cents
            #     currency='nad',
            #     metadata={
            #         'booking_id': booking.id,
            #         'payment_id': payment.id,
            #         'user_id': current_user_id
            #     }
            # )
            
            # Mock payment intent with proper Stripe format
            import secrets
            intent = {
                'id': f'pi_mock_{payment.id}',
                'client_secret': f'pi_mock_{payment.id}_secret_{secrets.token_hex(12)}',
                'amount': int(booking.total_amount * 100),
                'currency': 'nad',
                'status': 'requires_payment_method'
            }
            
            payment.payment_intent_id = intent['id']
            payment.payment_metadata = {
                'stripe_intent_id': intent['id'],
                'client_secret': intent['client_secret']
            }
            
            db.session.commit()
            
            return jsonify({
                'payment_intent': intent,
                'payment': payment.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Stripe error: {str(e)}")
            return jsonify({'error': 'Payment processing error'}), 500
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating payment intent: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@payments_bp.route('/confirm-payment', methods=['POST'])
@jwt_required()
def confirm_payment():
    """Confirm payment after Stripe processing"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('payment_intent_id'):
            return jsonify({'error': 'payment_intent_id is required'}), 400
        
        payment_intent_id = data['payment_intent_id']
        
        # Find payment record
        payment = Payment.query.filter_by(
            payment_intent_id=payment_intent_id,
            status='pending'
        ).first()
        
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        
        # Verify booking belongs to user
        if payment.booking.user_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Mock Stripe confirmation
        try:
            # In a real implementation, you would retrieve the payment intent from Stripe:
            # intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            # Mock successful payment
            intent = {
                'id': payment_intent_id,
                'status': 'succeeded',
                'charges': {
                    'data': [{
                        'id': f'ch_mock_{payment.id}',
                        'balance_transaction': f'txn_mock_{payment.id}'
                    }]
                }
            }
            
            if intent['status'] == 'succeeded':
                # Update payment status
                payment.status = 'completed'
                payment.processed_at = datetime.utcnow()
                payment.provider_transaction_id = intent['charges']['data'][0]['id']
                
                # Update booking status
                if payment.booking.status == 'pending':
                    payment.booking.status = 'confirmed'
                    payment.booking.confirmed_at = datetime.utcnow()
                
                # Create audit log
                audit_log = AuditLog(
                    table_name='payments',
                    record_id=payment.id,
                    action='UPDATE',
                    old_values={'status': 'pending'},
                    new_values={'status': 'completed', 'processed_at': payment.processed_at.isoformat()},
                    user_id=current_user_id,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(audit_log)
                
                db.session.commit()
                
                # Send payment confirmation email
                try:
                    from app.services.email_service import EmailService
                    EmailService.send_payment_confirmation(payment)
                except Exception as email_error:
                    current_app.logger.error(f"Failed to send payment confirmation email: {str(email_error)}")
                
                return jsonify({
                    'message': 'Payment confirmed successfully',
                    'payment': payment.to_dict(),
                    'booking': payment.booking.to_dict()
                })
            else:
                return jsonify({'error': 'Payment not completed'}), 400
                
        except Exception as e:
            current_app.logger.error(f"Stripe confirmation error: {str(e)}")
            return jsonify({'error': 'Payment confirmation failed'}), 500
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error confirming payment: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@payments_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks for payment events"""
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        
        webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
        if not webhook_secret or not sig_header:
            return jsonify({'error': 'Webhook verification is not configured'}), 503

        try:
            event_data = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except (ValueError, stripe.error.SignatureVerificationError):
            return jsonify({'error': 'Invalid webhook signature'}), 400

        event_type = event_data.get('type')
        
        if event_type == 'payment_intent.succeeded':
            payment_intent = event_data.get('data', {}).get('object', {})
            payment_intent_id = payment_intent.get('id')
            
            if not payment_intent_id:
                return jsonify({'error': 'No payment intent ID'}), 400
            
            # Find payment record
            payment = Payment.query.filter_by(
                payment_intent_id=payment_intent_id,
                status='pending'
            ).first()
            
            if not payment:
                return jsonify({'error': 'Payment not found'}), 404
            
            # Update payment status
            payment.status = 'completed'
            payment.processed_at = datetime.utcnow()
            payment.provider_transaction_id = payment_intent.get('charges', {}).get('data', [{}])[0].get('id', '')
            
            # Update booking status
            if payment.booking.status == 'pending':
                payment.booking.status = 'confirmed'
                payment.booking.confirmed_at = datetime.utcnow()
            
            # Create audit log
            audit_log = AuditLog(
                table_name='payments',
                record_id=payment.id,
                action='UPDATE',
                old_values={'status': 'pending'},
                new_values={'status': 'completed', 'processed_at': payment.processed_at.isoformat()},
                user_id=None,  # System action
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
            
            db.session.commit()
            
            return jsonify({'status': 'success'})
        
        elif event_type == 'payment_intent.payment_failed':
            payment_intent = event_data.get('data', {}).get('object', {})
            payment_intent_id = payment_intent.get('id')
            
            if payment_intent_id:
                payment = Payment.query.filter_by(
                    payment_intent_id=payment_intent_id,
                    status='pending'
                ).first()
                
                if payment:
                    payment.status = 'failed'
                    payment.processed_at = datetime.utcnow()
                    
                    # Create audit log
                    audit_log = AuditLog(
                        table_name='payments',
                        record_id=payment.id,
                        action='UPDATE',
                        old_values={'status': 'pending'},
                        new_values={'status': 'failed', 'processed_at': payment.processed_at.isoformat()},
                        user_id=None,
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
                    db.session.add(audit_log)
                    
                    db.session.commit()
            
            return jsonify({'status': 'success'})
        
        return jsonify({'status': 'ignored'})
        
    except Exception as e:
        current_app.logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': 'Webhook processing failed'}), 500

@payments_bp.route('/<int:payment_id>', methods=['GET'])
@jwt_required()
def get_payment(payment_id):
    """Get payment details"""
    try:
        current_user_id = get_jwt_identity()
        
        payment = Payment.query.get_or_404(payment_id)
        
        # Check if user owns the booking
        if payment.booking.user_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        return jsonify({'payment': payment.to_dict()})
        
    except Exception as e:
        current_app.logger.error(f"Error getting payment: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@payments_bp.route('/booking/<int:booking_id>', methods=['GET'])
@jwt_required()
def get_booking_payments(booking_id):
    """Get all payments for a booking"""
    try:
        current_user_id = get_jwt_identity()
        
        booking = Booking.query.filter_by(id=booking_id, user_id=current_user_id).first()
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        payments = Payment.query.filter_by(booking_id=booking_id).all()
        
        return jsonify({
            'booking': booking.to_dict(),
            'payments': [payment.to_dict() for payment in payments]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting booking payments: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@payments_bp.route('/<int:payment_id>/refund', methods=['POST'])
@jwt_required()
def refund_payment(payment_id):
    """Refund a payment (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user has admin role
        if not user or not user.has_role('admin'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        payment = Payment.query.get_or_404(payment_id)
        
        if payment.status != 'completed':
            return jsonify({'error': 'Payment must be completed to refund'}), 400
        
        data = request.get_json()
        refund_amount = data.get('amount', payment.amount) if data else payment.amount
        
        if refund_amount > payment.amount:
            return jsonify({'error': 'Refund amount cannot exceed payment amount'}), 400
        
        # Mock Stripe refund
        try:
            # In a real implementation:
            # refund = stripe.Refund.create(
            #     payment_intent=payment.payment_intent_id,
            #     amount=int(refund_amount * 100)  # Convert to cents
            # )
            
            # Mock successful refund
            refund = {
                'id': f're_mock_{payment.id}',
                'status': 'succeeded',
                'amount': int(refund_amount * 100)
            }
            
            # Create new payment record for refund
            refund_payment = Payment(
                booking_id=payment.booking_id,
                payment_reference=Payment().generate_payment_reference(),
                amount=-refund_amount,  # Negative amount for refund
                currency=payment.currency,
                payment_method='refund',
                payment_provider='stripe',
                status='completed',
                provider_transaction_id=refund['id'],
                processed_at=datetime.utcnow(),
                payment_metadata={'refund_for': payment.id, 'stripe_refund_id': refund['id']}
            )
            
            db.session.add(refund_payment)
            
            # Update original payment status
            payment.status = 'refunded'
            
            # Create audit log
            audit_log = AuditLog(
                table_name='payments',
                record_id=payment.id,
                action='UPDATE',
                old_values={'status': 'completed'},
                new_values={'status': 'refunded', 'refund_amount': float(refund_amount)},
                user_id=current_user_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
            
            db.session.commit()
            
            return jsonify({
                'message': 'Refund processed successfully',
                'refund': refund_payment.to_dict(),
                'original_payment': payment.to_dict()
            })
            
        except Exception as e:
            current_app.logger.error(f"Stripe refund error: {str(e)}")
            return jsonify({'error': 'Refund processing failed'}), 500
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing refund: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@payments_bp.route('/methods', methods=['GET'])
def get_payment_methods():
    """Get available payment methods"""
    return jsonify({
        'payment_methods': [
            {
                'id': 'card',
                'name': 'Credit/Debit Card',
                'provider': 'stripe',
                'enabled': True,
                'currencies': ['NAD', 'USD', 'EUR']
            },
            {
                'id': 'bank_transfer',
                'name': 'Bank Transfer',
                'provider': 'manual',
                'enabled': True,
                'currencies': ['NAD']
            }
        ]
    })
