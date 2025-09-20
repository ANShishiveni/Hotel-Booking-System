#!/usr/bin/env python3
"""
Seed script for populating the database with initial data
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.user import User, Role
from app.models.hotel import Hotel, RoomType, Room
from app.models.booking import Guest

def create_roles():
    """Create default roles"""
    roles = [
        {
            'name': 'admin',
            'description': 'Administrator with full system access',
            'permissions': [
                'admin_all', 'manage_users', 'manage_hotels', 
                'view_analytics', 'manage_bookings', 'process_payments'
            ]
        },
        {
            'name': 'customer',
            'description': 'Regular customer role',
            'permissions': [
                'book_room', 'view_bookings', 'write_reviews', 
                'manage_profile', 'process_payments'
            ]
        },
        {
            'name': 'hotel_manager',
            'description': 'Hotel manager role',
            'permissions': [
                'manage_hotel', 'view_bookings', 'manage_rooms',
                'view_analytics'
            ]
        }
    ]
    
    for role_data in roles:
        role = Role.query.filter_by(name=role_data['name']).first()
        if not role:
            role = Role(**role_data)
            db.session.add(role)
            print(f"Created role: {role_data['name']}")
    
    db.session.commit()

def create_admin_user():
    """Create admin user"""
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        print("Admin role not found. Please create roles first.")
        return
    
    admin_user = User.query.filter_by(email='admin@hotelbooking.com').first()
    if not admin_user:
        admin_user = User(
            email='admin@hotelbooking.com',
            first_name='Admin',
            last_name='User',
            phone='+1234567890',
            role_id=admin_role.id
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        print("Created admin user: admin@hotelbooking.com / admin123")
    
    db.session.commit()

def create_sample_hotels():
    """Create sample hotels with room types and rooms"""
    
    hotels_data = [
        {
            'name': 'Grand Plaza Hotel',
            'address': '123 Main Street',
            'city': 'New York',
            'state': 'NY',
            'country': 'USA',
            'postal_code': '10001',
            'phone': '+1-555-0123',
            'email': 'info@grandplaza.com',
            'latitude': Decimal('40.7128'),
            'longitude': Decimal('-74.0060'),
            'amenities': ['wifi', 'parking', 'pool', 'gym', 'restaurant', 'bar'],
            'room_types': [
                {
                    'name': 'Standard Room',
                    'description': 'Comfortable standard room with city view',
                    'max_occupancy': 2,
                    'amenities': ['wifi', 'tv', 'minibar'],
                    'base_price': Decimal('150.00'),
                    'pricing_rules': {'weekend_multiplier': 1.3},
                    'rooms': [
                        {'room_number': '101', 'floor': '1'},
                        {'room_number': '102', 'floor': '1'},
                        {'room_number': '103', 'floor': '1'},
                        {'room_number': '104', 'floor': '1'},
                        {'room_number': '105', 'floor': '1'},
                    ]
                },
                {
                    'name': 'Deluxe Suite',
                    'description': 'Spacious suite with premium amenities',
                    'max_occupancy': 4,
                    'amenities': ['wifi', 'tv', 'minibar', 'jacuzzi', 'balcony'],
                    'base_price': Decimal('300.00'),
                    'pricing_rules': {'weekend_multiplier': 1.4},
                    'rooms': [
                        {'room_number': '201', 'floor': '2'},
                        {'room_number': '202', 'floor': '2'},
                        {'room_number': '203', 'floor': '2'},
                    ]
                }
            ]
        },
        {
            'name': 'Ocean View Resort',
            'address': '456 Beach Boulevard',
            'city': 'Miami',
            'state': 'FL',
            'country': 'USA',
            'postal_code': '33101',
            'phone': '+1-555-0456',
            'email': 'info@oceanviewresort.com',
            'latitude': Decimal('25.7617'),
            'longitude': Decimal('-80.1918'),
            'amenities': ['wifi', 'parking', 'beach_access', 'pool', 'spa', 'restaurant'],
            'room_types': [
                {
                    'name': 'Ocean View Room',
                    'description': 'Room with stunning ocean views',
                    'max_occupancy': 2,
                    'amenities': ['wifi', 'tv', 'ocean_view', 'balcony'],
                    'base_price': Decimal('200.00'),
                    'pricing_rules': {'weekend_multiplier': 1.5},
                    'rooms': [
                        {'room_number': '301', 'floor': '3'},
                        {'room_number': '302', 'floor': '3'},
                        {'room_number': '303', 'floor': '3'},
                        {'room_number': '304', 'floor': '3'},
                    ]
                },
                {
                    'name': 'Penthouse Suite',
                    'description': 'Luxurious penthouse with panoramic ocean views',
                    'max_occupancy': 6,
                    'amenities': ['wifi', 'tv', 'ocean_view', 'balcony', 'kitchen', 'jacuzzi'],
                    'base_price': Decimal('500.00'),
                    'pricing_rules': {'weekend_multiplier': 1.6},
                    'rooms': [
                        {'room_number': '501', 'floor': '5'},
                    ]
                }
            ]
        },
        {
            'name': 'Mountain Lodge',
            'address': '789 Alpine Trail',
            'city': 'Denver',
            'state': 'CO',
            'country': 'USA',
            'postal_code': '80202',
            'phone': '+1-555-0789',
            'email': 'info@mountainlodge.com',
            'latitude': Decimal('39.7392'),
            'longitude': Decimal('-104.9903'),
            'amenities': ['wifi', 'parking', 'fireplace', 'restaurant', 'hiking_trails'],
            'room_types': [
                {
                    'name': 'Mountain View Cabin',
                    'description': 'Rustic cabin with mountain views',
                    'max_occupancy': 3,
                    'amenities': ['wifi', 'tv', 'fireplace', 'mountain_view'],
                    'base_price': Decimal('120.00'),
                    'pricing_rules': {'weekend_multiplier': 1.2},
                    'rooms': [
                        {'room_number': 'C1', 'floor': '1'},
                        {'room_number': 'C2', 'floor': '1'},
                        {'room_number': 'C3', 'floor': '1'},
                        {'room_number': 'C4', 'floor': '1'},
                        {'room_number': 'C5', 'floor': '1'},
                        {'room_number': 'C6', 'floor': '1'},
                    ]
                }
            ]
        }
    ]
    
    for hotel_data in hotels_data:
        # Create hotel
        hotel = Hotel.query.filter_by(name=hotel_data['name']).first()
        if not hotel:
            room_types_data = hotel_data.pop('room_types')
            hotel = Hotel(**hotel_data)
            db.session.add(hotel)
            db.session.flush()  # Get hotel ID
            
            print(f"Created hotel: {hotel.name}")
            
            # Create room types and rooms
            for room_type_data in room_types_data:
                rooms_data = room_type_data.pop('rooms')
                room_type = RoomType(hotel_id=hotel.id, **room_type_data)
                db.session.add(room_type)
                db.session.flush()  # Get room type ID
                
                print(f"  Created room type: {room_type.name}")
                
                # Create rooms
                for room_data in rooms_data:
                    room = Room(
                        hotel_id=hotel.id,
                        room_type_id=room_type.id,
                        room_number=room_data['room_number'],
                        floor=room_data['floor'],
                        features={'created_by': 'seed_script'}
                    )
                    db.session.add(room)
                
                print(f"    Created {len(rooms_data)} rooms")
    
    db.session.commit()

def create_sample_guests():
    """Create sample guests"""
    guests_data = [
        {
            'first_name': 'John',
            'last_name': 'Smith',
            'email': 'john.smith@email.com',
            'phone': '+1-555-1001',
            'nationality': 'US',
            'date_of_birth': datetime(1985, 6, 15).date()
        },
        {
            'first_name': 'Emily',
            'last_name': 'Johnson',
            'email': 'emily.johnson@email.com',
            'phone': '+1-555-1002',
            'nationality': 'US',
            'date_of_birth': datetime(1990, 3, 22).date()
        },
        {
            'first_name': 'Michael',
            'last_name': 'Brown',
            'email': 'michael.brown@email.com',
            'phone': '+1-555-1003',
            'nationality': 'CA',
            'date_of_birth': datetime(1988, 11, 8).date()
        },
        {
            'first_name': 'Sarah',
            'last_name': 'Davis',
            'email': 'sarah.davis@email.com',
            'phone': '+1-555-1004',
            'nationality': 'UK',
            'date_of_birth': datetime(1992, 9, 14).date()
        }
    ]
    
    for guest_data in guests_data:
        guest = Guest.query.filter_by(email=guest_data['email']).first()
        if not guest:
            guest = Guest(**guest_data)
            db.session.add(guest)
            print(f"Created guest: {guest.full_name}")
    
    db.session.commit()

def main():
    """Main seeding function"""
    app = create_app('development')
    
    with app.app_context():
        print("Starting database seeding...")
        
        # Create tables if they don't exist
        db.create_all()
        
        # Create roles
        print("\n1. Creating roles...")
        create_roles()
        
        # Create admin user
        print("\n2. Creating admin user...")
        create_admin_user()
        
        # Create sample hotels
        print("\n3. Creating sample hotels...")
        create_sample_hotels()
        
        # Create sample guests
        print("\n4. Creating sample guests...")
        create_sample_guests()
        
        print("\n✅ Database seeding completed successfully!")
        print("\nYou can now:")
        print("- Login as admin: admin@hotelbooking.com / admin123")
        print("- Access the API at: http://localhost:5000/api")
        print("- Check health status at: http://localhost:5000/health")

if __name__ == '__main__':
    main()
