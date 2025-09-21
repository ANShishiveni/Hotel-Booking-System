#!/usr/bin/env python3
"""
Simple startup script for the Hotel Booking System
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def main():
    """Start the Flask application"""
    print("🏨 Starting Hotel Booking System...")
    print("=" * 50)
    
    # Create Flask application
    app = create_app('DevelopmentConfig')
    
    print("✅ Application created successfully!")
    print("\n🌐 Application URLs:")
    print("   Main Website: http://localhost:5000")
    print("   API Endpoints: http://localhost:5000/api/")
    print("   Admin Panel: http://localhost:5000/admin")
    print("\n🔑 Test Login Credentials:")
    print("   Admin: admin@namibiahotels.com / admin123")
    print("   Staff: staff@namibiahotels.com / staff123")
    print("   Guest: john.doe@example.com / password123")
    print("\n📁 Database: SQLite (hotel_booking_dev.db)")
    print("🚀 Starting server...")
    print("=" * 50)
    
    try:
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")

if __name__ == '__main__':
    main()
