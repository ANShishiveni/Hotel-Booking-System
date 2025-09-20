"""
Admin routes for system management and analytics
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, limiter
from app.models.user import User, Role
from app.models.hotel import Hotel, Room, RoomType
from app.models.booking import Booking, Guest
from app.models.payment import Payment
from app.models.review import Review
from app.models.audit import AuditLog
from app.utils.decorators import validate_json, require_permissions
from app.utils.validators import validate_email
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@require_permissions(['admin_all'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Get date range (default to last 30 days)
        days = request.args.get('days', 30, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Booking statistics
        total_bookings = Booking.query.count()
        recent_bookings = Booking.query.filter(
            Booking.created_at >= start_date
        ).count()
        
        # Revenue statistics
        total_revenue = db.session.query(func.sum(Payment.amount)).filter(
            Payment.status == 'completed'
        ).scalar() or 0
        
        recent_revenue = db.session.query(func.sum(Payment.amount)).filter(
            and_(
                Payment.status == 'completed',
                Payment.created_at >= start_date
            )
        ).scalar() or 0
        
        # Occupancy statistics
        total_rooms = Room.query.filter_by(is_active=True).count()
        
        # Get occupancy for recent period
        occupied_rooms = db.session.query(func.count(BookingRoom.id.distinct())).join(Booking).filter(
            and_(
                Booking.status.in_(['confirmed', 'checked_in']),
                Booking.check_in <= end_date,
                Booking.check_out >= start_date
            )
        ).scalar() or 0
        
        occupancy_rate = (occupied_rooms / (total_rooms * days)) * 100 if total_rooms > 0 else 0
        
        # User statistics
        total_users = User.query.filter_by(is_active=True).count()
        recent_users = User.query.filter(
            User.created_at >= start_date
        ).count()
        
        # Review statistics
        total_reviews = Review.query.count()
        avg_rating = db.session.query(func.avg(Review.rating)).scalar() or 0
        
        return jsonify({
            'dashboard_stats': {
                'bookings': {
                    'total': total_bookings,
                    'recent': recent_bookings,
                    'growth_rate': ((recent_bookings / days) / max(total_bookings / 365, 1)) * 100
                },
                'revenue': {
                    'total': float(total_revenue),
                    'recent': float(recent_revenue),
                    'growth_rate': ((recent_revenue / days) / max(total_revenue / 365, 1)) * 100
                },
                'occupancy': {
                    'rate': round(occupancy_rate, 2),
                    'total_rooms': total_rooms,
                    'occupied_rooms': occupied_rooms
                },
                'users': {
                    'total': total_users,
                    'recent': recent_users
                },
                'reviews': {
                    'total': total_reviews,
                    'average_rating': round(float(avg_rating), 2)
                }
            },
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Dashboard stats error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve dashboard stats'}), 500

@admin_bp.route('/bookings', methods=['GET'])
@jwt_required()
@require_permissions(['admin_all'])
def get_all_bookings():
    """Get all bookings with filtering"""
    try:
        # Get query parameters
        status = request.args.get('status')
        hotel_id = request.args.get('hotel_id', type=int)
        user_id = request.args.get('user_id', type=int)
        check_in_from = request.args.get('check_in_from')
        check_in_to = request.args.get('check_in_to')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = Booking.query
        
        if status:
            query = query.filter_by(status=status)
        
        if hotel_id:
            query = query.filter_by(hotel_id=hotel_id)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if check_in_from:
            check_in_from_dt = datetime.strptime(check_in_from, '%Y-%m-%d')
            query = query.filter(Booking.check_in >= check_in_from_dt)
        
        if check_in_to:
            check_in_to_dt = datetime.strptime(check_in_to, '%Y-%m-%d')
            query = query.filter(Booking.check_in <= check_in_to_dt)
        
        # Order by creation date (newest first)
        query = query.order_by(Booking.created_at.desc())
        
        # Apply pagination
        bookings = query.offset(offset).limit(limit).all()
        total = query.count()
        
        return jsonify({
            'bookings': [booking.to_dict(include_rooms=True, include_payments=True) for booking in bookings],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get all bookings error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve bookings'}), 500

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@require_permissions(['admin_all'])
def get_all_users():
    """Get all users with filtering"""
    try:
        # Get query parameters
        role = request.args.get('role')
        is_active = request.args.get('is_active')
        search = request.args.get('search')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = User.query
        
        if role:
            query = query.join(Role).filter(Role.name == role)
        
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            query = query.filter_by(is_active=is_active_bool)
        
        if search:
            search_filter = or_(
                User.email.ilike(f'%{search}%'),
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        # Order by creation date (newest first)
        query = query.order_by(User.created_at.desc())
        
        # Apply pagination
        users = query.offset(offset).limit(limit).all()
        total = query.count()
        
        return jsonify({
            'users': [user.to_dict(include_sensitive=True) for user in users],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get all users error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve users'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@require_permissions(['admin_all'])
@validate_json(['is_active', 'role_id'])
def update_user(user_id):
    """Update user status and role (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Validate role
        role = Role.query.get(data['role_id'])
        if not role:
            return jsonify({'error': 'Invalid role'}), 400
        
        # Update user
        user.is_active = data['is_active']
        user.role_id = data['role_id']
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict(include_sensitive=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update user error: {str(e)}")
        return jsonify({'error': 'User update failed'}), 500

@admin_bp.route('/hotels/<int:hotel_id>/toggle', methods=['POST'])
@jwt_required()
@require_permissions(['admin_all'])
def toggle_hotel_status(hotel_id):
    """Toggle hotel active status (admin only)"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        
        hotel.is_active = not hotel.is_active
        db.session.commit()
        
        status = "activated" if hotel.is_active else "deactivated"
        
        return jsonify({
            'message': f'Hotel {status} successfully',
            'hotel': hotel.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Toggle hotel status error: {str(e)}")
        return jsonify({'error': 'Hotel status update failed'}), 500

@admin_bp.route('/payments', methods=['GET'])
@jwt_required()
@require_permissions(['admin_all'])
def get_all_payments():
    """Get all payments with filtering"""
    try:
        # Get query parameters
        status = request.args.get('status')
        payment_method = request.args.get('payment_method')
        booking_id = request.args.get('booking_id', type=int)
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = Payment.query
        
        if status:
            query = query.filter_by(status=status)
        
        if payment_method:
            query = query.filter_by(payment_method=payment_method)
        
        if booking_id:
            query = query.filter_by(booking_id=booking_id)
        
        # Order by creation date (newest first)
        query = query.order_by(Payment.created_at.desc())
        
        # Apply pagination
        payments = query.offset(offset).limit(limit).all()
        total = query.count()
        
        return jsonify({
            'payments': [payment.to_dict(include_sensitive=True) for payment in payments],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get all payments error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve payments'}), 500

@admin_bp.route('/audit-logs', methods=['GET'])
@jwt_required()
@require_permissions(['admin_all'])
def get_audit_logs():
    """Get audit logs with filtering"""
    try:
        # Get query parameters
        table_name = request.args.get('table_name')
        user_id = request.args.get('user_id', type=int)
        action = request.args.get('action')
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = AuditLog.query
        
        if table_name:
            query = query.filter_by(table_name=table_name)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if action:
            query = query.filter_by(action=action)
        
        # Filter by time range
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(AuditLog.created_at >= cutoff_time)
        
        # Order by creation date (newest first)
        query = query.order_by(AuditLog.created_at.desc())
        
        # Apply pagination
        logs = query.offset(offset).limit(limit).all()
        total = query.count()
        
        return jsonify({
            'audit_logs': [log.to_dict() for log in logs],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get audit logs error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve audit logs'}), 500

@admin_bp.route('/reports/revenue', methods=['GET'])
@jwt_required()
@require_permissions(['admin_all'])
def get_revenue_report():
    """Generate revenue report"""
    try:
        # Get date range
        days = request.args.get('days', 30, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get daily revenue
        daily_revenue = db.session.query(
            func.date(Payment.created_at).label('date'),
            func.sum(Payment.amount).label('revenue'),
            func.count(Payment.id).label('transactions')
        ).filter(
            and_(
                Payment.status == 'completed',
                Payment.created_at >= start_date,
                Payment.created_at <= end_date
            )
        ).group_by(func.date(Payment.created_at)).all()
        
        # Get revenue by payment method
        method_revenue = db.session.query(
            Payment.payment_method,
            func.sum(Payment.amount).label('revenue'),
            func.count(Payment.id).label('transactions')
        ).filter(
            and_(
                Payment.status == 'completed',
                Payment.created_at >= start_date,
                Payment.created_at <= end_date
            )
        ).group_by(Payment.payment_method).all()
        
        return jsonify({
            'revenue_report': {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'daily_revenue': [
                    {
                        'date': day.date.isoformat(),
                        'revenue': float(day.revenue),
                        'transactions': day.transactions
                    }
                    for day in daily_revenue
                ],
                'method_revenue': [
                    {
                        'payment_method': method.payment_method,
                        'revenue': float(method.revenue),
                        'transactions': method.transactions
                    }
                    for method in method_revenue
                ]
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Revenue report error: {str(e)}")
        return jsonify({'error': 'Failed to generate revenue report'}), 500
