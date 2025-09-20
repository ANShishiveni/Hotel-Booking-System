"""
Validation utilities for the Hotel Booking System
"""

import re
from datetime import datetime, timedelta

def validate_email(email):
    """Validate email format"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if not password:
        return "Password is required"
    
    if len(password) < 8:
        return "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return "Password must be less than 128 characters"
    
    if not re.search(r'[A-Z]', password):
        return "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return "Password must contain at least one special character"
    
    return None

def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return True  # Phone is optional
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (7-15 digits)
    if len(digits_only) < 7 or len(digits_only) > 15:
        return False
    
    return True

def validate_booking_dates(check_in, check_out):
    """Validate booking dates"""
    try:
        # Parse dates
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        
        # Check if dates are valid
        today = datetime.utcnow().date()
        
        if check_in_date < today:
            return "Check-in date cannot be in the past"
        
        if check_out_date <= check_in_date:
            return "Check-out date must be after check-in date"
        
        # Check maximum advance booking (1 year)
        max_advance = today + timedelta(days=365)
        if check_in_date > max_advance:
            return "Cannot book more than 1 year in advance"
        
        # Check minimum stay (1 night)
        if (check_out_date - check_in_date).days < 1:
            return "Minimum stay is 1 night"
        
        # Check maximum stay (30 nights)
        if (check_out_date - check_in_date).days > 30:
            return "Maximum stay is 30 nights"
        
        return None
        
    except ValueError:
        return "Invalid date format. Use YYYY-MM-DD"

def validate_occupancy(adults, children=0):
    """Validate occupancy numbers"""
    if not isinstance(adults, int) or adults <= 0:
        return "Adults must be a positive integer"
    
    if not isinstance(children, int) or children < 0:
        return "Children must be a non-negative integer"
    
    if adults > 10:
        return "Maximum 10 adults per booking"
    
    if children > 10:
        return "Maximum 10 children per booking"
    
    total_occupancy = adults + children
    if total_occupancy > 15:
        return "Maximum total occupancy is 15 people"
    
    return None

def validate_rating(rating):
    """Validate review rating"""
    if not isinstance(rating, int):
        return "Rating must be an integer"
    
    if not (1 <= rating <= 5):
        return "Rating must be between 1 and 5"
    
    return None

def validate_room_selection(room_selections):
    """Validate room selection data"""
    if not isinstance(room_selections, list):
        return "Room selections must be a list"
    
    if len(room_selections) == 0:
        return "At least one room must be selected"
    
    if len(room_selections) > 10:
        return "Maximum 10 rooms per booking"
    
    for selection in room_selections:
        if not isinstance(selection, dict):
            return "Each room selection must be an object"
        
        required_fields = ['room_type_id', 'quantity']
        for field in required_fields:
            if field not in selection:
                return f"Room selection missing required field: {field}"
        
        if not isinstance(selection['room_type_id'], int):
            return "Room type ID must be an integer"
        
        if not isinstance(selection['quantity'], int) or selection['quantity'] <= 0:
            return "Room quantity must be a positive integer"
        
        if selection['quantity'] > 5:
            return "Maximum 5 rooms of the same type per booking"
    
    return None

def validate_guest_info(guest_info):
    """Validate guest information"""
    required_fields = ['first_name', 'last_name']
    for field in required_fields:
        if field not in guest_info:
            return f"Guest information missing required field: {field}"
        
        if not guest_info[field] or not isinstance(guest_info[field], str):
            return f"Guest {field} must be a non-empty string"
        
        if len(guest_info[field]) > 50:
            return f"Guest {field} must be less than 50 characters"
    
    # Validate email if provided
    if guest_info.get('email') and not validate_email(guest_info['email']):
        return "Invalid guest email format"
    
    # Validate phone if provided
    if guest_info.get('phone') and not validate_phone(guest_info['phone']):
        return "Invalid guest phone format"
    
    # Validate date of birth if provided
    if guest_info.get('date_of_birth'):
        try:
            dob = datetime.strptime(guest_info['date_of_birth'], '%Y-%m-%d').date()
            today = datetime.utcnow().date()
            
            if dob > today:
                return "Date of birth cannot be in the future"
            
            # Check if person is at least 18 years old
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                return "Guest must be at least 18 years old"
            
        except ValueError:
            return "Invalid date of birth format. Use YYYY-MM-DD"
    
    return None

def sanitize_string(text, max_length=None):
    """Sanitize string input"""
    if not isinstance(text, str):
        return ""
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    
    # Limit length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text

def validate_pagination_params(limit, offset):
    """Validate pagination parameters"""
    if not isinstance(limit, int) or limit <= 0:
        return "Limit must be a positive integer"
    
    if limit > 100:
        return "Limit cannot exceed 100"
    
    if not isinstance(offset, int) or offset < 0:
        return "Offset must be a non-negative integer"
    
    return None
