"""
Custom decorators for the Hotel Booking System
"""

from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User

def validate_json(required_fields):
    """Decorator to validate JSON request data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body cannot be empty'}), 400
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_permissions(required_permissions):
    """Decorator to check user permissions"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if not user.is_active:
                return jsonify({'error': 'Account is deactivated'}), 403
            
            # Check if user has any of the required permissions
            user_permissions = user.role.permissions if user.role else []
            has_permission = any(perm in user_permissions for perm in required_permissions)
            
            if not has_permission:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_admin(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.is_admin():
            return jsonify({'error': 'Admin privileges required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def rate_limit_by_user(max_requests=100, window=3600):
    """Decorator for user-specific rate limiting"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            # Rate limiting logic would be implemented here
            # For now, just pass through
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_timezone(f):
    """Decorator to validate and set timezone"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        timezone = request.headers.get('X-Timezone', 'UTC')
        
        # Validate timezone
        try:
            import pytz
            pytz.timezone(timezone)
            request.timezone = timezone
        except pytz.exceptions.UnknownTimeZoneError:
            request.timezone = 'UTC'
        
        return f(*args, **kwargs)
    return decorated_function
