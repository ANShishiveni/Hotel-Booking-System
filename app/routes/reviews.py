"""
Review routes for managing hotel reviews and ratings
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, limiter
from app.models.user import User
from app.models.booking import Booking
from app.models.review import Review
from app.utils.decorators import validate_json, require_permissions
from datetime import datetime

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route('/', methods=['GET'])
@limiter.limit("60 per minute")
def get_reviews():
    """Get reviews with filtering options"""
    try:
        # Get query parameters
        hotel_id = request.args.get('hotel_id', type=int)
        user_id = request.args.get('user_id', type=int)
        rating = request.args.get('rating', type=int)
        verified_only = request.args.get('verified_only', 'false').lower() == 'true'
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = Review.query
        
        if hotel_id:
            query = query.join(Booking).filter(Booking.hotel_id == hotel_id)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if rating:
            query = query.filter_by(rating=rating)
        
        if verified_only:
            query = query.filter_by(is_verified=True)
        
        # Order by creation date (newest first)
        query = query.order_by(Review.created_at.desc())
        
        # Apply pagination
        reviews = query.offset(offset).limit(limit).all()
        total = query.count()
        
        return jsonify({
            'reviews': [review.to_dict(include_booking_details=True) for review in reviews],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get reviews error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve reviews'}), 500

@reviews_bp.route('/hotel/<int:hotel_id>', methods=['GET'])
@limiter.limit("60 per minute")
def get_hotel_reviews(hotel_id):
    """Get reviews for a specific hotel"""
    try:
        # Get query parameters
        rating = request.args.get('rating', type=int)
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = Review.query.join(Booking).filter(Booking.hotel_id == hotel_id)
        
        if rating:
            query = query.filter_by(rating=rating)
        
        # Order by creation date (newest first)
        query = query.order_by(Review.created_at.desc())
        
        # Apply pagination
        reviews = query.offset(offset).limit(limit).all()
        total = query.count()
        
        # Calculate average rating
        avg_rating = db.session.query(db.func.avg(Review.rating)).join(Booking).filter(
            Booking.hotel_id == hotel_id
        ).scalar() or 0
        
        # Get rating distribution
        rating_distribution = db.session.query(
            Review.rating,
            db.func.count(Review.id).label('count')
        ).join(Booking).filter(
            Booking.hotel_id == hotel_id
        ).group_by(Review.rating).all()
        
        rating_dist = {str(i): 0 for i in range(1, 6)}
        for rating_val, count in rating_distribution:
            rating_dist[str(rating_val)] = count
        
        return jsonify({
            'hotel_id': hotel_id,
            'average_rating': round(float(avg_rating), 2),
            'total_reviews': total,
            'rating_distribution': rating_dist,
            'reviews': [review.to_dict(include_booking_details=True) for review in reviews],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get hotel reviews error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve hotel reviews'}), 500

@reviews_bp.route('/<int:review_id>', methods=['GET'])
@limiter.limit("60 per minute")
def get_review(review_id):
    """Get specific review details"""
    try:
        review = Review.query.get_or_404(review_id)
        
        return jsonify({
            'review': review.to_dict(include_booking_details=True)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get review error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve review'}), 500

@reviews_bp.route('/', methods=['POST'])
@jwt_required()
@limiter.limit("5 per minute")
@validate_json(['booking_id', 'rating', 'title', 'comment'])
def create_review():
    """Create a new review"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate rating
        if not (1 <= data['rating'] <= 5):
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        # Get booking
        booking = Booking.query.get_or_404(data['booking_id'])
        
        # Check if user owns this booking
        if booking.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if booking is completed
        if booking.status != 'checked_out':
            return jsonify({'error': 'Can only review completed bookings'}), 400
        
        # Check if review already exists
        existing_review = Review.query.filter_by(
            booking_id=booking.id,
            user_id=current_user_id
        ).first()
        
        if existing_review:
            return jsonify({'error': 'Review already exists for this booking'}), 409
        
        # Create review
        review = Review(
            booking_id=booking.id,
            user_id=current_user_id,
            rating=data['rating'],
            title=data['title'],
            comment=data['comment'],
            is_verified=True  # Verified since it's from a completed booking
        )
        
        db.session.add(review)
        db.session.commit()
        
        return jsonify({
            'message': 'Review created successfully',
            'review': review.to_dict(include_booking_details=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create review error: {str(e)}")
        return jsonify({'error': 'Review creation failed'}), 500

@reviews_bp.route('/<int:review_id>', methods=['PUT'])
@jwt_required()
@validate_json(['rating', 'title', 'comment'])
def update_review(review_id):
    """Update a review"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate rating
        if not (1 <= data['rating'] <= 5):
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        # Get review
        review = Review.query.get_or_404(review_id)
        
        # Check if user owns this review
        if review.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if review can be edited
        if not review.can_be_edited:
            return jsonify({'error': 'Review can no longer be edited'}), 400
        
        # Update review
        review.rating = data['rating']
        review.title = data['title']
        review.comment = data['comment']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Review updated successfully',
            'review': review.to_dict(include_booking_details=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update review error: {str(e)}")
        return jsonify({'error': 'Review update failed'}), 500

@reviews_bp.route('/<int:review_id>', methods=['DELETE'])
@jwt_required()
def delete_review(review_id):
    """Delete a review"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get review
        review = Review.query.get_or_404(review_id)
        
        # Check if user owns this review or is admin
        if review.user_id != current_user_id and not _is_admin(current_user_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if review can be edited (for non-admin users)
        if not _is_admin(current_user_id) and not review.can_be_edited:
            return jsonify({'error': 'Review can no longer be deleted'}), 400
        
        db.session.delete(review)
        db.session.commit()
        
        return jsonify({'message': 'Review deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete review error: {str(e)}")
        return jsonify({'error': 'Review deletion failed'}), 500

@reviews_bp.route('/<int:review_id>/verify', methods=['POST'])
@jwt_required()
@require_permissions(['admin_all'])
def verify_review(review_id):
    """Verify a review (admin only)"""
    try:
        review = Review.query.get_or_404(review_id)
        
        review.is_verified = True
        db.session.commit()
        
        return jsonify({
            'message': 'Review verified successfully',
            'review': review.to_dict(include_booking_details=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Verify review error: {str(e)}")
        return jsonify({'error': 'Review verification failed'}), 500

@reviews_bp.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_reviews(user_id):
    """Get reviews by a specific user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Check if user is requesting their own reviews or is admin
        if user_id != current_user_id and not _is_admin(current_user_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Get query parameters
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = Review.query.filter_by(user_id=user_id)
        
        # Order by creation date (newest first)
        query = query.order_by(Review.created_at.desc())
        
        # Apply pagination
        reviews = query.offset(offset).limit(limit).all()
        total = query.count()
        
        return jsonify({
            'user_id': user_id,
            'reviews': [review.to_dict(include_booking_details=True) for review in reviews],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get user reviews error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve user reviews'}), 500

def _is_admin(user_id):
    """Check if user is admin"""
    user = User.query.get(user_id)
    return user and user.is_admin()
