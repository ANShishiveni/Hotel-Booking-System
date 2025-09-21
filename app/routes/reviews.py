from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Hotel, Booking, Review, AuditLog
from app import db
from datetime import datetime, date
from sqlalchemy import and_, func, desc

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route('/', methods=['GET'])
def get_reviews():
    """Get all reviews with filtering and pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        hotel_id = request.args.get('hotel_id', type=int)
        rating = request.args.get('rating', type=int)
        verified_only = request.args.get('verified_only', 'false').lower() == 'true'
        
        # Build query
        query = Review.query.filter_by(is_active=True)
        
        if hotel_id:
            query = query.filter_by(hotel_id=hotel_id)
        
        if rating:
            query = query.filter_by(rating=rating)
        
        if verified_only:
            query = query.filter_by(is_verified=True)
        
        reviews = query.order_by(desc(Review.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'reviews': [review.to_dict() for review in reviews.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': reviews.total,
                'pages': reviews.pages,
                'has_next': reviews.has_next,
                'has_prev': reviews.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting reviews: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reviews_bp.route('/<int:review_id>', methods=['GET'])
def get_review(review_id):
    """Get specific review details"""
    try:
        review = Review.query.get_or_404(review_id)
        
        if not review.is_active:
            return jsonify({'error': 'Review not found'}), 404
        
        return jsonify({'review': review.to_dict()})
        
    except Exception as e:
        current_app.logger.error(f"Error getting review: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reviews_bp.route('/', methods=['POST'])
@jwt_required()
def create_review():
    """Create a new review"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['hotel_id', 'rating', 'comment']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        hotel_id = data['hotel_id']
        rating = data['rating']
        comment = data['comment'].strip()
        title = data.get('title', '').strip()
        booking_id = data.get('booking_id')
        
        # Validate rating
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({'error': 'Rating must be an integer between 1 and 5'}), 400
        
        # Check if hotel exists
        hotel = Hotel.query.get(hotel_id)
        if not hotel or not hotel.is_active:
            return jsonify({'error': 'Hotel not found'}), 404
        
        # If booking_id provided, verify user has a completed booking
        if booking_id:
            booking = Booking.query.filter_by(
                id=booking_id,
                user_id=current_user_id,
                hotel_id=hotel_id,
                status='checked_out'
            ).first()
            
            if not booking:
                return jsonify({'error': 'Invalid booking for review'}), 400
            
            # Check if review already exists for this booking
            existing_review = Review.query.filter_by(
                hotel_id=hotel_id,
                user_id=current_user_id,
                booking_id=booking_id
            ).first()
            
            if existing_review:
                return jsonify({'error': 'Review already exists for this booking'}), 409
        else:
            # Check if user has any completed bookings at this hotel
            has_booking = Booking.query.filter_by(
                user_id=current_user_id,
                hotel_id=hotel_id,
                status='checked_out'
            ).first()
            
            if not has_booking:
                return jsonify({'error': 'You must have stayed at this hotel to leave a review'}), 403
            
            # Check if user already reviewed this hotel
            existing_review = Review.query.filter_by(
                hotel_id=hotel_id,
                user_id=current_user_id
            ).first()
            
            if existing_review:
                return jsonify({'error': 'You have already reviewed this hotel'}), 409
        
        # Create review
        review = Review(
            hotel_id=hotel_id,
            user_id=current_user_id,
            booking_id=booking_id,
            rating=rating,
            title=title,
            comment=comment,
            is_verified=bool(booking_id)  # Verified if linked to booking
        )
        
        db.session.add(review)
        db.session.commit()
        
        # Create audit log
        audit_log = AuditLog(
            table_name='reviews',
            record_id=review.id,
            action='CREATE',
            new_values=review.to_dict(),
            user_id=current_user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'message': 'Review created successfully',
            'review': review.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating review: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reviews_bp.route('/<int:review_id>', methods=['PUT'])
@jwt_required()
def update_review(review_id):
    """Update a review (only by the author)"""
    try:
        current_user_id = get_jwt_identity()
        
        review = Review.query.get_or_404(review_id)
        
        if review.user_id != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if not review.is_active:
            return jsonify({'error': 'Review not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Store old values
        old_values = review.to_dict()
        
        # Update allowed fields
        if 'rating' in data:
            rating = data['rating']
            if not isinstance(rating, int) or rating < 1 or rating > 5:
                return jsonify({'error': 'Rating must be an integer between 1 and 5'}), 400
            review.rating = rating
        
        if 'title' in data:
            review.title = data['title'].strip()
        
        if 'comment' in data:
            comment = data['comment'].strip()
            if not comment:
                return jsonify({'error': 'Comment cannot be empty'}), 400
            review.comment = comment
        
        db.session.commit()
        
        # Create audit log
        audit_log = AuditLog(
            table_name='reviews',
            record_id=review.id,
            action='UPDATE',
            old_values=old_values,
            new_values=review.to_dict(),
            user_id=current_user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'message': 'Review updated successfully',
            'review': review.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating review: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reviews_bp.route('/<int:review_id>', methods=['DELETE'])
@jwt_required()
def delete_review(review_id):
    """Delete a review (soft delete)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        review = Review.query.get_or_404(review_id)
        
        # Allow deletion by author or admin
        if review.user_id != current_user_id and not (user and user.has_role('admin')):
            return jsonify({'error': 'Unauthorized'}), 403
        
        if not review.is_active:
            return jsonify({'error': 'Review not found'}), 404
        
        # Soft delete
        review.is_active = False
        
        # Create audit log
        audit_log = AuditLog(
            table_name='reviews',
            record_id=review.id,
            action='DELETE',
            old_values=review.to_dict(),
            new_values={'is_active': False},
            user_id=current_user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({'message': 'Review deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting review: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reviews_bp.route('/hotel/<int:hotel_id>/stats', methods=['GET'])
def get_hotel_review_stats(hotel_id):
    """Get review statistics for a hotel"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        
        if not hotel.is_active:
            return jsonify({'error': 'Hotel not found'}), 404
        
        # Calculate statistics
        stats = db.session.query(
            func.count(Review.id).label('total_reviews'),
            func.avg(Review.rating).label('average_rating'),
            func.min(Review.rating).label('min_rating'),
            func.max(Review.rating).label('max_rating')
        ).filter_by(hotel_id=hotel_id, is_active=True).first()
        
        # Rating distribution
        rating_dist = db.session.query(
            Review.rating,
            func.count(Review.id).label('count')
        ).filter_by(hotel_id=hotel_id, is_active=True)\
         .group_by(Review.rating)\
         .order_by(Review.rating)\
         .all()
        
        rating_distribution = {str(rating): count for rating, count in rating_dist}
        
        # Recent reviews
        recent_reviews = Review.query.filter_by(hotel_id=hotel_id, is_active=True)\
            .order_by(desc(Review.created_at))\
            .limit(5).all()
        
        return jsonify({
            'hotel': hotel.to_dict(),
            'statistics': {
                'total_reviews': stats.total_reviews or 0,
                'average_rating': float(stats.average_rating) if stats.average_rating else 0,
                'min_rating': stats.min_rating or 0,
                'max_rating': stats.max_rating or 0,
                'rating_distribution': rating_distribution
            },
            'recent_reviews': [review.to_dict() for review in recent_reviews]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting review stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reviews_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_reviews(user_id):
    """Get all reviews by a specific user"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        user = User.query.get_or_404(user_id)
        
        reviews = Review.query.filter_by(user_id=user_id, is_active=True)\
            .order_by(desc(Review.created_at))\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'user': user.to_dict(),
            'reviews': [review.to_dict() for review in reviews.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': reviews.total,
                'pages': reviews.pages,
                'has_next': reviews.has_next,
                'has_prev': reviews.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting user reviews: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@reviews_bp.route('/<int:review_id>/verify', methods=['POST'])
@jwt_required()
def verify_review(review_id):
    """Verify a review (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Check if user has admin role
        if not user or not user.has_role('admin'):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        review = Review.query.get_or_404(review_id)
        
        if not review.is_active:
            return jsonify({'error': 'Review not found'}), 404
        
        review.is_verified = True
        
        # Create audit log
        audit_log = AuditLog(
            table_name='reviews',
            record_id=review.id,
            action='UPDATE',
            old_values={'is_verified': False},
            new_values={'is_verified': True},
            user_id=current_user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'message': 'Review verified successfully',
            'review': review.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error verifying review: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
