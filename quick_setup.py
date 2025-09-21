#!/usr/bin/env python3
"""
Quick Setup Script for Hotel Booking System
This script sets up the system with SQLite for easy local development
"""

import os
import sys

def create_env_file():
    """Create .env file with SQLite configuration"""
    env_content = """# Flask Configuration
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production

# Database Configuration (SQLite for easy setup)
DATABASE_URL=sqlite:///hotel_booking_prod.db
DEV_DATABASE_URL=sqlite:///hotel_booking_dev.db
TEST_DATABASE_URL=sqlite:///hotel_booking_test.db

# JWT Configuration
JWT_SECRET_KEY=dev-jwt-secret-change-in-production

# Email Configuration (Mailpit for development)
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USE_TLS=false
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=noreply@hotelbooking.com

# Stripe Configuration (for production)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Application Settings
TIMEZONE=Africa/Windhoek
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# Redis Configuration (for rate limiting)
REDIS_URL=redis://localhost:6379/0

# Rate Limiting
RATELIMIT_STORAGE_URL=memory://
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file with SQLite configuration")

def setup_database():
    """Initialize the database with sample data"""
    try:
        from app import create_app, db
        from init_db import main as init_db_main
        
        print("🚀 Initializing database...")
        init_db_main()
        print("✅ Database initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False
    
    return True

def test_application():
    """Test if the application can start"""
    try:
        from app import create_app
        
        app = create_app()
        print("✅ Application can be created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating application: {e}")
        return False

def main():
    """Main setup function"""
    print("🏨 Hotel Booking System - Quick Setup")
    print("=" * 50)
    
    # Step 1: Create .env file
    print("\n[1/4] Creating environment configuration...")
    create_env_file()
    
    # Step 2: Test application
    print("\n[2/4] Testing application...")
    if not test_application():
        print("❌ Setup failed at application test")
        return False
    
    # Step 3: Setup database
    print("\n[3/4] Setting up database...")
    if not setup_database():
        print("❌ Setup failed at database initialization")
        return False
    
    # Step 4: Final instructions
    print("\n[4/4] Setup completed!")
    print("\n" + "=" * 50)
    print("🎉 Your Hotel Booking System is ready!")
    print("\n🌐 To start the application, run:")
    print("   python run.py")
    print("\n🔗 The application will be available at:")
    print("   http://localhost:5000")
    print("\n🔑 Sample Login Credentials:")
    print("   Admin: admin@namibiahotels.com / admin123")
    print("   Staff: staff@namibiahotels.com / staff123")
    print("   Guest: john.doe@example.com / password123")
    print("\n📁 Database files created:")
    print("   - hotel_booking_dev.db (SQLite database)")
    print("\n✨ Enjoy your hotel booking system!")

if __name__ == '__main__':
    main()
