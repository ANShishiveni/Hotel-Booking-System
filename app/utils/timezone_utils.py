"""
Timezone utilities for the Hotel Booking System
"""

import pytz
from datetime import datetime, timezone
from flask import request

def get_user_timezone(request_obj=None):
    """Get user timezone from request headers or default to UTC"""
    if request_obj is None:
        request_obj = request
    
    # Try to get timezone from headers
    timezone_str = request_obj.headers.get('X-Timezone', 'UTC')
    
    # Validate timezone
    try:
        pytz.timezone(timezone_str)
        return timezone_str
    except pytz.exceptions.UnknownTimeZoneError:
        return 'UTC'

def convert_to_utc(dt, from_timezone='UTC'):
    """Convert datetime from given timezone to UTC"""
    if dt is None:
        return None
    
    # If datetime is naive, assume it's in the given timezone
    if dt.tzinfo is None:
        tz = pytz.timezone(from_timezone)
        dt = tz.localize(dt)
    
    # Convert to UTC
    return dt.astimezone(pytz.UTC)

def convert_from_utc(dt, to_timezone='UTC'):
    """Convert datetime from UTC to given timezone"""
    if dt is None:
        return None
    
    # Ensure datetime is timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    
    # Convert to target timezone
    tz = pytz.timezone(to_timezone)
    return dt.astimezone(tz)

def format_datetime_for_user(dt, timezone_str='UTC', format_str='%Y-%m-%d %H:%M:%S'):
    """Format datetime for user display in their timezone"""
    if dt is None:
        return None
    
    # Convert to user timezone
    user_dt = convert_from_utc(dt, timezone_str)
    
    # Format for display
    return user_dt.strftime(format_str)

def get_local_date_range(check_in_str, check_out_str, timezone_str='UTC'):
    """Get local date range for booking dates"""
    try:
        # Parse dates as local dates in the given timezone
        tz = pytz.timezone(timezone_str)
        
        # Parse as naive dates first
        check_in_date = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        
        # Convert to timezone-aware datetime (start of day)
        check_in_dt = tz.localize(datetime.combine(check_in_date, datetime.min.time()))
        check_out_dt = tz.localize(datetime.combine(check_out_date, datetime.min.time()))
        
        # Convert to UTC
        check_in_utc = check_in_dt.astimezone(pytz.UTC)
        check_out_utc = check_out_dt.astimezone(pytz.UTC)
        
        return check_in_utc, check_out_utc
        
    except ValueError:
        raise ValueError("Invalid date format. Use YYYY-MM-DD")

def is_business_hours(dt, timezone_str='UTC', business_start=9, business_end=17):
    """Check if datetime is within business hours"""
    if dt is None:
        return False
    
    # Convert to local timezone
    local_dt = convert_from_utc(dt, timezone_str)
    
    # Check if it's a weekday (Monday = 0, Sunday = 6)
    if local_dt.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Check if it's within business hours
    hour = local_dt.hour
    return business_start <= hour < business_end

def get_next_business_day(dt, timezone_str='UTC'):
    """Get the next business day from the given datetime"""
    if dt is None:
        dt = datetime.utcnow()
    
    # Convert to local timezone
    local_dt = convert_from_utc(dt, timezone_str)
    
    # Find next business day
    next_day = local_dt + timedelta(days=1)
    
    # Skip weekends
    while next_day.weekday() >= 5:  # Saturday or Sunday
        next_day += timedelta(days=1)
    
    # Return as UTC
    return convert_to_utc(next_day, timezone_str)

def calculate_duration_nights(check_in, check_out):
    """Calculate duration in nights between two dates"""
    if check_in is None or check_out is None:
        return 0
    
    # Ensure both dates are timezone-aware
    if check_in.tzinfo is None:
        check_in = check_in.replace(tzinfo=pytz.UTC)
    if check_out.tzinfo is None:
        check_out = check_out.replace(tzinfo=pytz.UTC)
    
    # Calculate difference
    duration = check_out - check_in
    return duration.days

def get_timezone_offset(timezone_str='UTC'):
    """Get timezone offset in hours from UTC"""
    try:
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
        offset = now.utcoffset()
        return offset.total_seconds() / 3600
    except pytz.exceptions.UnknownTimeZoneError:
        return 0

def format_duration(duration_seconds):
    """Format duration in human-readable format"""
    if duration_seconds < 60:
        return f"{duration_seconds} seconds"
    elif duration_seconds < 3600:
        minutes = duration_seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif duration_seconds < 86400:
        hours = duration_seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''}"
    else:
        days = duration_seconds // 86400
        return f"{days} day{'s' if days != 1 else ''}"
