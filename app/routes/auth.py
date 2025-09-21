from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt, verify_jwt_in_request
)
from werkzeug.security import check_password_hash
from app.models import User, Role, TokenBlacklist, AuditLog
from app import db
from datetime import datetime
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, "Valid password"

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'username', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        email = data['email'].strip().lower()
        username = data['username'].strip()
        password = data['password']
        first_name = data['first_name'].strip()
        last_name = data['last_name'].strip()
        phone = data.get('phone', '').strip()
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        is_valid_password, password_message = validate_password(password)
        if not is_valid_password:
            return jsonify({'error': password_message}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already taken'}), 409
        
        # Create new user
        user = User(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone=phone
        )
        user.set_password(password)
        
        # Assign guest role by default
        guest_role = Role.query.filter_by(name='guest').first()
        if guest_role:
            user.roles.append(guest_role)
        
        db.session.add(user)
        db.session.commit()
        
        # Create audit log
        audit_log = AuditLog(
            table_name='users',
            record_id=user.id,
            action='CREATE',
            new_values=user.to_dict(),
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()
        
        # Generate tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in user registration: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT tokens"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 403
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in user login: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        new_access_token = create_access_token(identity=current_user_id)
        
        return jsonify({
            'access_token': new_access_token
        })
        
    except Exception as e:
        current_app.logger.error(f"Error refreshing token: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user by blacklisting tokens"""
    try:
        jti = get_jwt()['jti']
        token_type = get_jwt()['type']
        user_id = get_jwt_identity()
        
        # Add token to blacklist
        blacklisted_token = TokenBlacklist(
            jti=jti,
            token_type=token_type,
            user_id=user_id
        )
        db.session.add(blacklisted_token)
        db.session.commit()
        
        return jsonify({'message': 'Successfully logged out'})
        
    except Exception as e:
        current_app.logger.error(f"Error in logout: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()})
        
    except Exception as e:
        current_app.logger.error(f"Error getting profile: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Store old values for audit log
        old_values = user.to_dict()
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name'].strip()
        
        if 'last_name' in data:
            user.last_name = data['last_name'].strip()
        
        if 'phone' in data:
            user.phone = data['phone'].strip()
        
        if 'email' in data:
            new_email = data['email'].strip().lower()
            if not validate_email(new_email):
                return jsonify({'error': 'Invalid email format'}), 400
            
            # Check if email is already taken by another user
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({'error': 'Email already taken'}), 409
            
            user.email = new_email
            user.email_verified = False  # Require re-verification
        
        db.session.commit()
        
        # Create audit log
        audit_log = AuditLog(
            table_name='users',
            record_id=user.id,
            action='UPDATE',
            old_values=old_values,
            new_values=user.to_dict(),
            user_id=current_user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating profile: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data or not all(k in data for k in ['current_password', 'new_password']):
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        # Verify current password
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Validate new password
        is_valid_password, password_message = validate_password(new_password)
        if not is_valid_password:
            return jsonify({'error': password_message}), 400
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        # Create audit log
        audit_log = AuditLog(
            table_name='users',
            record_id=user.id,
            action='UPDATE',
            old_values={'password_changed': True},
            new_values={'password_changed': True},
            user_id=current_user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error changing password: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/verify-email', methods=['POST'])
@jwt_required()
def verify_email():
    """Verify user email (mock implementation)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # In a real application, you would send a verification email
        # For now, we'll just mark it as verified
        user.email_verified = True
        db.session.commit()
        
        return jsonify({'message': 'Email verification sent'})
        
    except Exception as e:
        current_app.logger.error(f"Error sending email verification: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Send password reset email"""
    try:
        data = request.get_json()
        if not data or not data.get('email'):
            return jsonify({'error': 'Email is required'}), 400
        
        email = data['email'].strip().lower()
        user = User.query.filter_by(email=email).first()
        
        # Always return success to prevent email enumeration
        # In a real application, you would send a reset email
        return jsonify({'message': 'If the email exists, a password reset link has been sent'})
        
    except Exception as e:
        current_app.logger.error(f"Error in forgot password: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token"""
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ['token', 'new_password']):
            return jsonify({'error': 'Token and new password are required'}), 400
        
        # In a real application, you would validate the reset token
        # For now, we'll return an error
        return jsonify({'error': 'Password reset functionality not implemented'}), 501
        
    except Exception as e:
        current_app.logger.error(f"Error resetting password: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
