#!/usr/bin/env python3
"""
Database Initialization Script

This script initializes the database with sample data for development and testing.
Run this script after setting up the database to populate it with initial data.
"""

import os
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import User, Role, Hotel, RoomType, Room, Booking, Guest, Review

def create_roles():
    """Create default roles"""
    print("Creating roles...")
    
    roles_data = [
        {
            'name': 'admin',
            'description': 'System Administrator',
            'permissions': ['all']
        },
        {
            'name': 'staff',
            'description': 'Hotel Staff',
            'permissions': ['manage_bookings', 'view_reports', 'manage_rooms']
        },
        {
            'name': 'guest',
            'description': 'Guest User',
            'permissions': ['book_rooms', 'write_reviews', 'manage_profile']
        }
    ]
    
    for role_data in roles_data:
        role = Role.query.filter_by(name=role_data['name']).first()
        if not role:
            role = Role(**role_data)
            db.session.add(role)
            print(f"  ✓ Created role: {role_data['name']}")
        else:
            print(f"  - Role already exists: {role_data['name']}")
    
    db.session.commit()

def create_users():
    """Create sample users"""
    print("Creating users...")
    
    # Admin user
    admin_user = User.query.filter_by(email='admin@namibiahotels.com').first()
    if not admin_user:
        admin_user = User(
            email='admin@namibiahotels.com',
            username='admin',
            first_name='System',
            last_name='Administrator',
            phone='+264612345678'
        )
        admin_user.set_password('admin123')
        admin_user.email_verified = True
        admin_user.is_active = True
        db.session.add(admin_user)
        
        # Assign admin role
        admin_role = Role.query.filter_by(name='admin').first()
        if admin_role:
            admin_user.roles.append(admin_role)
        
        print("  ✓ Created admin user: admin@namibiahotels.com (password: admin123)")
    else:
        print("  - Admin user already exists")
    
    # Staff user
    staff_user = User.query.filter_by(email='staff@namibiahotels.com').first()
    if not staff_user:
        staff_user = User(
            email='staff@namibiahotels.com',
            username='staff',
            first_name='Hotel',
            last_name='Staff',
            phone='+264612345679'
        )
        staff_user.set_password('staff123')
        staff_user.email_verified = True
        staff_user.is_active = True
        db.session.add(staff_user)
        
        # Assign staff role
        staff_role = Role.query.filter_by(name='staff').first()
        if staff_role:
            staff_user.roles.append(staff_role)
        
        print("  ✓ Created staff user: staff@namibiahotels.com (password: staff123)")
    else:
        print("  - Staff user already exists")
    
    # Sample guest users
    guest_users_data = [
        {
            'email': 'john.doe@example.com',
            'username': 'johndoe',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+264612345680'
        },
        {
            'email': 'jane.smith@example.com',
            'username': 'janesmith',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone': '+264612345681'
        },
        {
            'email': 'mike.wilson@example.com',
            'username': 'mikewilson',
            'first_name': 'Mike',
            'last_name': 'Wilson',
            'phone': '+264612345682'
        }
    ]
    
    guest_role = Role.query.filter_by(name='guest').first()
    
    for user_data in guest_users_data:
        user = User.query.filter_by(email=user_data['email']).first()
        if not user:
            user = User(**user_data)
            user.set_password('password123')
            user.email_verified = True
            user.is_active = True
            db.session.add(user)
            
            # Assign guest role
            if guest_role:
                user.roles.append(guest_role)
            
            print(f"  ✓ Created guest user: {user_data['email']} (password: password123)")
        else:
            print(f"  - User already exists: {user_data['email']}")
    
    db.session.commit()

def create_hotels():
    """Create sample hotels"""
    print("Creating hotels...")
    
    hotels_data = [
        {
            'name': 'Namibia Luxury Hotel',
            'description': 'Experience unparalleled luxury in the heart of Windhoek. Our 5-star hotel offers world-class amenities, exceptional service, and stunning views of the city.',
            'address': '123 Independence Avenue',
            'city': 'Windhoek',
            'state': 'Khomas',
            'country': 'Namibia',
            'postal_code': '9000',
            'phone': '+264612345000',
            'email': 'info@namibialuxury.com',
            'website': 'https://www.namibialuxury.com',
            'latitude': -22.5609,
            'longitude': 17.0658,
            'star_rating': 5,
            'amenities': ['WiFi', 'Pool', 'Spa', 'Restaurant', 'Gym', 'Business Center', 'Parking'],
            'images': [
                'https://images.unsplash.com/photo-1566073771259-6a8506099945?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
                'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
            ],
            'policies': {
                'check_in': '14:00',
                'check_out': '11:00',
                'cancellation': 'Free cancellation up to 24 hours before check-in',
                'pets': 'Pets allowed with additional fee',
                'smoking': 'Non-smoking property'
            }
        },
        {
            'name': 'Swakopmund Beach Resort',
            'description': 'Located on the pristine beaches of Swakopmund, our resort offers a perfect blend of coastal beauty and modern comfort.',
            'address': '456 Beach Road',
            'city': 'Swakopmund',
            'state': 'Erongo',
            'country': 'Namibia',
            'postal_code': '9001',
            'phone': '+264642345000',
            'email': 'info@swakopresort.com',
            'website': 'https://www.swakopresort.com',
            'latitude': -22.6783,
            'longitude': 14.5266,
            'star_rating': 4,
            'amenities': ['WiFi', 'Pool', 'Beach Access', 'Restaurant', 'Bar', 'Parking'],
            'images': [
                'https://images.unsplash.com/photo-1571896349842-33c89424de2d?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
                'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
            ],
            'policies': {
                'check_in': '15:00',
                'check_out': '11:00',
                'cancellation': 'Free cancellation up to 48 hours before check-in',
                'pets': 'Pets not allowed',
                'smoking': 'Non-smoking property'
            }
        },
        {
            'name': 'Etosha Safari Lodge',
            'description': 'Immerse yourself in the wild beauty of Namibia at our safari lodge near Etosha National Park.',
            'address': '789 Safari Road',
            'city': 'Outjo',
            'state': 'Kunene',
            'country': 'Namibia',
            'postal_code': '9002',
            'phone': '+264672345000',
            'email': 'info@etoshasafari.com',
            'website': 'https://www.etoshasafari.com',
            'latitude': -20.4614,
            'longitude': 16.6478,
            'star_rating': 4,
            'amenities': ['WiFi', 'Restaurant', 'Bar', 'Safari Tours', 'Parking', 'Airport Shuttle'],
            'images': [
                'https://images.unsplash.com/photo-1584132967334-10e028bd69f7?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80',
                'https://images.unsplash.com/photo-1578662996442-48f60103fc96?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
            ],
            'policies': {
                'check_in': '14:00',
                'check_out': '10:00',
                'cancellation': 'Free cancellation up to 7 days before check-in',
                'pets': 'Pets not allowed',
                'smoking': 'Non-smoking property'
            }
        }
    ]
    
    for hotel_data in hotels_data:
        hotel = Hotel.query.filter_by(name=hotel_data['name']).first()
        if not hotel:
            hotel = Hotel(**hotel_data)
            db.session.add(hotel)
            print(f"  ✓ Created hotel: {hotel_data['name']}")
        else:
            print(f"  - Hotel already exists: {hotel_data['name']}")
    
    db.session.commit()

def create_room_types():
    """Create sample room types"""
    print("Creating room types...")
    
    hotels = Hotel.query.all()
    
    room_types_data = [
        {
            'name': 'Standard Room',
            'description': 'Comfortable standard room with modern amenities',
            'base_price': Decimal('150.00'),
            'max_occupancy': 2,
            'bed_type': 'Queen',
            'room_size': 25,
            'amenities': ['WiFi', 'TV', 'Air Conditioning', 'Mini-bar', 'Safe']
        },
        {
            'name': 'Deluxe Room',
            'description': 'Spacious deluxe room with premium amenities',
            'base_price': Decimal('250.00'),
            'max_occupancy': 2,
            'bed_type': 'King',
            'room_size': 35,
            'amenities': ['WiFi', 'TV', 'Air Conditioning', 'Mini-bar', 'Safe', 'Balcony', 'Ocean View']
        },
        {
            'name': 'Executive Suite',
            'description': 'Luxurious suite with separate living area',
            'base_price': Decimal('450.00'),
            'max_occupancy': 4,
            'bed_type': 'King',
            'room_size': 65,
            'amenities': ['WiFi', 'TV', 'Air Conditioning', 'Mini-bar', 'Safe', 'Balcony', 'Ocean View', 'Living Room', 'Kitchenette']
        },
        {
            'name': 'Presidential Suite',
            'description': 'Ultimate luxury with panoramic views',
            'base_price': Decimal('750.00'),
            'max_occupancy': 6,
            'bed_type': 'King',
            'room_size': 120,
            'amenities': ['WiFi', 'TV', 'Air Conditioning', 'Mini-bar', 'Safe', 'Balcony', 'Panoramic View', 'Living Room', 'Kitchen', 'Butler Service']
        }
    ]
    
    for hotel in hotels:
        for room_type_data in room_types_data:
            # Adjust pricing based on hotel star rating
            multiplier = hotel.star_rating / 5.0
            adjusted_price = room_type_data['base_price'] * Decimal(str(multiplier))
            
            room_type = RoomType.query.filter_by(
                hotel_id=hotel.id,
                name=room_type_data['name']
            ).first()
            
            if not room_type:
                room_type_data_copy = room_type_data.copy()
                room_type_data_copy['base_price'] = adjusted_price
                
                room_type = RoomType(
                    hotel_id=hotel.id,
                    **room_type_data_copy
                )
                db.session.add(room_type)
                print(f"  ✓ Created room type: {room_type_data['name']} at {hotel.name}")
    
    db.session.commit()

def create_rooms():
    """Create sample rooms"""
    print("Creating rooms...")
    
    room_types = RoomType.query.all()
    
    for room_type in room_types:
        # Create 5-10 rooms per room type
        num_rooms = 8 if 'Suite' in room_type.name else 12
        
        for i in range(1, num_rooms + 1):
            room_number = f"{100 + i}"
            floor = 1 if i <= 6 else 2
            
            room = Room.query.filter_by(
                hotel_id=room_type.hotel_id,
                room_number=room_number
            ).first()
            
            if not room:
                room = Room(
                    hotel_id=room_type.hotel_id,
                    room_type_id=room_type.id,
                    room_number=room_number,
                    floor=floor
                )
                db.session.add(room)
        
        print(f"  ✓ Created {num_rooms} rooms for {room_type.name}")
    
    db.session.commit()

def create_sample_bookings():
    """Create sample bookings"""
    print("Creating sample bookings...")
    
    users = User.query.filter(User.email.like('%@example.com')).all()
    hotels = Hotel.query.all()
    
    if not users or not hotels:
        print("  - No users or hotels found, skipping sample bookings")
        return
    
    # Create some past bookings
    for i, user in enumerate(users):
        hotel = hotels[i % len(hotels)]
        room_type = RoomType.query.filter_by(hotel_id=hotel.id).first()
        room = Room.query.filter_by(hotel_id=hotel.id, room_type_id=room_type.id).first()
        
        if room_type and room:
            # Past booking
            check_in = date.today() - timedelta(days=30 + i*5)
            check_out = check_in + timedelta(days=2)
            nights = (check_out - check_in).days
            
            booking = Booking(
                booking_reference=Booking().generate_booking_reference(),
                user_id=user.id,
                hotel_id=hotel.id,
                room_id=room.id,
                room_type_id=room_type.id,
                check_in_date=check_in,
                check_out_date=check_out,
                nights=nights,
                adults=2,
                children=0,
                room_rate=float(room_type.base_price),
                total_amount=float(room_type.base_price) * nights * 1.15,  # Including tax
                tax_amount=float(room_type.base_price) * nights * 0.15,
                discount_amount=0,
                status='checked_out',
                confirmed_at=datetime.utcnow() - timedelta(days=35 + i*5),
                created_at=datetime.utcnow() - timedelta(days=40 + i*5)
            )
            db.session.add(booking)
            
            # Create guest
            guest = Guest(
                booking_id=booking.id,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                phone=user.phone,
                is_primary_guest=True
            )
            db.session.add(guest)
            
            print(f"  ✓ Created booking for {user.first_name} {user.last_name} at {hotel.name}")
    
    db.session.commit()

def create_sample_reviews():
    """Create sample reviews"""
    print("Creating sample reviews...")
    
    # Get bookings that are checked out
    bookings = Booking.query.filter_by(status='checked_out').all()
    
    for booking in bookings:
        # Create a review for each booking
        existing_review = Review.query.filter_by(
            hotel_id=booking.hotel_id,
            user_id=booking.user_id,
            booking_id=booking.id
        ).first()
        
        if not existing_review:
            rating = 4 + (booking.id % 2)  # 4 or 5 stars
            review = Review(
                hotel_id=booking.hotel_id,
                user_id=booking.user_id,
                booking_id=booking.id,
                rating=rating,
                title=f'Great stay at {booking.hotel.name}' if rating == 5 else f'Good experience at {booking.hotel.name}',
                comment=f'We had a wonderful time at {booking.hotel.name}. The service was excellent and the room was very comfortable.' if rating == 5 else f'Our stay at {booking.hotel.name} was pleasant. The facilities were good and the staff was friendly.',
                is_verified=True,
                created_at=booking.created_at + timedelta(days=1)
            )
            db.session.add(review)
            print(f"  ✓ Created review for {booking.hotel.name}")
    
    db.session.commit()

def main():
    """Main initialization function"""
    print("🏨 Initializing Hotel Booking System Database...")
    print("=" * 50)
    
    # Create Flask app
    app = create_app('DevelopmentConfig')
    
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("✅ Database tables created")
        print()
        
        # Create sample data
        create_roles()
        print()
        create_users()
        print()
        create_hotels()
        print()
        create_room_types()
        print()
        create_rooms()
        print()
        create_sample_bookings()
        print()
        create_sample_reviews()
        print()
        
        print("=" * 50)
        print("✅ Database initialization completed successfully!")
        print()
        print("📋 Sample Accounts Created:")
        print("  Admin: admin@namibiahotels.com / admin123")
        print("  Staff: staff@namibiahotels.com / staff123")
        print("  Guest: john.doe@example.com / password123")
        print("  Guest: jane.smith@example.com / password123")
        print("  Guest: mike.wilson@example.com / password123")
        print()
        print("🏨 Sample Hotels Created:")
        hotels = Hotel.query.all()
        for hotel in hotels:
            print(f"  - {hotel.name} ({hotel.star_rating}★) in {hotel.city}")
        print()
        print("🚀 You can now start the application with: python run.py")

if __name__ == '__main__':
    main()
