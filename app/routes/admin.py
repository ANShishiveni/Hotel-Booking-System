from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Role, Hotel, Booking, Payment, Review, AuditLog
from app import db
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, func, desc
import csv
import io

admin_bp = Blueprint('admin', __name__)

def require_admin():
    """Decorator to require admin role"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.has_role('admin'):
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    return None

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def admin_dashboard():
    """Get admin dashboard statistics"""
    try:
        # Check admin permissions
        permission_error = require_admin()
        if permission_error:
            return permission_error
        
        # Get date range (default to last 30 days)
        days = request.args.get('days', 30, type=int)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Basic statistics
        stats = {
            'total_hotels': Hotel.query.filter_by(is_active=True).count(),
            'total_users': User.query.filter_by(is_active=True).count(),
            'total_bookings': Booking.query.count(),
            'total_revenue': db.session.query(func.sum(Payment.amount))\
                .filter(Payment.status == 'completed').scalar() or 0,
            'pending_bookings': Booking.query.filter_by(status='pending').count(),
            'active_reviews': Review.query.filter_by(is_active=True).count()
        }
        
        # Revenue by month (last 12 months)
        revenue_by_month = db.session.query(
            func.date_trunc('month', Payment.processed_at).label('month'),
            func.sum(Payment.amount).label('revenue')
        ).filter(
            Payment.status == 'completed',
            Payment.processed_at >= start_date
        ).group_by('month').order_by('month').all()
        
        # Bookings by status
        bookings_by_status = db.session.query(
            Booking.status,
            func.count(Booking.id).label('count')
        ).group_by(Booking.status).all()
        
        # Top hotels by bookings
        top_hotels = db.session.query(
            Hotel.name,
            Hotel.id,
            func.count(Booking.id).label('booking_count')
        ).join(Booking, Booking.hotel_id == Hotel.id)\
         .filter(Booking.created_at >= start_date)\
         .group_by(Hotel.id, Hotel.name)\
         .order_by(desc('booking_count'))\
         .limit(10).all()
        
        # Recent activities (audit logs)
        recent_activities = AuditLog.query\
            .order_by(desc(AuditLog.created_at))\
            .limit(20).all()
        
        return jsonify({
            'statistics': stats,
            'revenue_by_month': [
                {'month': month.strftime('%Y-%m'), 'revenue': float(revenue)}
                for month, revenue in revenue_by_month
            ],
            'bookings_by_status': [
                {'status': status, 'count': count}
                for status, count in bookings_by_status
            ],
            'top_hotels': [
                {'hotel_id': hotel_id, 'name': name, 'booking_count': count}
                for name, hotel_id, count in top_hotels
            ],
            'recent_activities': [activity.to_dict() for activity in recent_activities],
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting admin dashboard: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users with filtering and pagination"""
    try:
        # Check admin permissions
        permission_error = require_admin()
        if permission_error:
            return permission_error
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        role = request.args.get('role', '')
        is_active = request.args.get('is_active')
        
        # Build query
        query = User.query
        
        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%'),
                    User.first_name.ilike(f'%{search}%'),
                    User.last_name.ilike(f'%{search}%')
                )
            )
        
        if role:
            query = query.join(User.roles).filter(Role.name == role)
        
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            query = query.filter(User.is_active == is_active_bool)
        
        users = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': users.total,
                'pages': users.pages,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting users: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/users/<int:user_id>/roles', methods=['PUT'])
@jwt_required()
def update_user_roles(user_id):
    """Update user roles"""
    try:
        # Check admin permissions
        permission_error = require_admin()
        if permission_error:
            return permission_error
        
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if not data or 'roles' not in data:
            return jsonify({'error': 'roles array is required'}), 400
        
        # Validate roles
        role_names = data['roles']
        roles = Role.query.filter(Role.name.in_(role_names)).all()
        
        if len(roles) != len(role_names):
            return jsonify({'error': 'One or more roles not found'}), 400
        
        # Update user roles
        user.roles = roles
        db.session.commit()
        
        # Create audit log
        audit_log = AuditLog(
            table_name='users',
            record_id=user.id,
            action='UPDATE',
            old_values={'roles': [role.name for role in user.roles]},
            new_values={'roles': role_names},
            user_id=get_jwt_identity(),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'message': 'User roles updated successfully',
            'user': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating user roles: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/bookings', methods=['GET'])
@jwt_required()
def get_all_bookings():
    """Get all bookings with filtering"""
    try:
        # Check admin permissions
        permission_error = require_admin()
        if permission_error:
            return permission_error
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '')
        hotel_id = request.args.get('hotel_id', type=int)
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # Build query
        query = Booking.query
        
        if status:
            query = query.filter_by(status=status)
        
        if hotel_id:
            query = query.filter_by(hotel_id=hotel_id)
        
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Booking.check_in_date >= start_dt)
        
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Booking.check_out_date <= end_dt)
        
        bookings = query.order_by(desc(Booking.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'bookings': [booking.to_dict() for booking in bookings.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': bookings.total,
                'pages': bookings.pages,
                'has_next': bookings.has_next,
                'has_prev': bookings.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting bookings: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/bookings/export', methods=['GET'])
@jwt_required()
def export_bookings():
    """Export bookings to CSV"""
    try:
        # Check admin permissions
        permission_error = require_admin()
        if permission_error:
            return permission_error
        
        # Get filter parameters
        status = request.args.get('status', '')
        hotel_id = request.args.get('hotel_id', type=int)
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # Build query
        query = Booking.query
        
        if status:
            query = query.filter_by(status=status)
        
        if hotel_id:
            query = query.filter_by(hotel_id=hotel_id)
        
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Booking.check_in_date >= start_dt)
        
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Booking.check_out_date <= end_dt)
        
        bookings = query.order_by(desc(Booking.created_at)).all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Booking ID', 'Reference', 'Hotel', 'Room', 'Guest', 'Email',
            'Check In', 'Check Out', 'Nights', 'Adults', 'Children',
            'Total Amount', 'Status', 'Created At'
        ])
        
        # Write data
        for booking in bookings:
            primary_guest = booking.guests.filter_by(is_primary_guest=True).first()
            writer.writerow([
                booking.id,
                booking.booking_reference,
                booking.hotel.name,
                booking.room.room_number,
                f"{primary_guest.first_name} {primary_guest.last_name}" if primary_guest else '',
                primary_guest.email if primary_guest else '',
                booking.check_in_date.isoformat(),
                booking.check_out_date.isoformat(),
                booking.nights,
                booking.adults,
                booking.children,
                booking.total_amount,
                booking.status,
                booking.created_at.isoformat()
            ])
        
        output.seek(0)
        csv_data = output.getvalue()
        output.close()
        
        return jsonify({
            'csv_data': csv_data,
            'filename': f'bookings_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            'record_count': len(bookings)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error exporting bookings: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/payments', methods=['GET'])
@jwt_required()
def get_all_payments():
    """Get all payments with filtering"""
    try:
        # Check admin permissions
        permission_error = require_admin()
        if permission_error:
            return permission_error
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '')
        payment_method = request.args.get('payment_method', '')
        
        # Build query
        query = Payment.query
        
        if status:
            query = query.filter_by(status=status)
        
        if payment_method:
            query = query.filter_by(payment_method=payment_method)
        
        payments = query.order_by(desc(Payment.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'payments': [payment.to_dict() for payment in payments.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': payments.total,
                'pages': payments.pages,
                'has_next': payments.has_next,
                'has_prev': payments.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting payments: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/audit-logs', methods=['GET'])
@jwt_required()
def get_audit_logs():
    """Get audit logs with filtering"""
    try:
        # Check admin permissions
        permission_error = require_admin()
        if permission_error:
            return permission_error
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        table_name = request.args.get('table_name', '')
        action = request.args.get('action', '')
        user_id = request.args.get('user_id', type=int)
        
        # Build query
        query = AuditLog.query
        
        if table_name:
            query = query.filter_by(table_name=table_name)
        
        if action:
            query = query.filter_by(action=action)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        logs = query.order_by(desc(AuditLog.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'audit_logs': [log.to_dict() for log in logs.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': logs.total,
                'pages': logs.pages,
                'has_next': logs.has_next,
                'has_prev': logs.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting audit logs: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/system-settings', methods=['GET'])
@jwt_required()
def get_system_settings():
    """Get system settings"""
    try:
        # Check admin permissions
        permission_error = require_admin()
        if permission_error:
            return permission_error
        
        # In a real application, these would come from a settings table
        settings = {
            'booking_cancellation_policy': {
                'same_day_fee': 1.0,  # 100% fee
                'one_two_days_fee': 0.5,  # 50% fee
                'three_six_days_fee': 0.25,  # 25% fee
                'seven_plus_days_fee': 0.0  # No fee
            },
            'payment_settings': {
                'default_currency': 'NAD',
                'tax_rate': 0.15,  # 15% VAT
                'supported_currencies': ['NAD', 'USD', 'EUR']
            },
            'email_settings': {
                'booking_confirmation': True,
                'payment_confirmation': True,
                'cancellation_notification': True
            }
        }
        
        return jsonify({'settings': settings})
        
    except Exception as e:
        current_app.logger.error(f"Error getting system settings: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/system-settings', methods=['PUT'])
@jwt_required()
def update_system_settings():
    """Update system settings"""
    try:
        # Check admin permissions
        permission_error = require_admin()
        if permission_error:
            return permission_error
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # In a real application, you would update a settings table
        # For now, we'll just return success
        
        return jsonify({'message': 'System settings updated successfully'})
        
    except Exception as e:
        current_app.logger.error(f"Error updating system settings: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
