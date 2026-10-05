#!/usr/bin/env python3
"""
Hotel Booking System - Main Application Entry Point

This script initializes and runs the Flask application.
It can be used for development, testing, and production deployment.
"""

import os
from app import create_app, db
# from flask_migrate import upgrade  # Optional: only needed if using Flask-Migrate

def create_tables():
    """Create database tables if they don't exist"""
    try:
        db.create_all()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")

def run_migrations():
    """Run database migrations"""
    try:
        # Check if migrations folder exists
        if not os.path.exists('migrations'):
            print("INFO: No migrations folder found, skipping migrations")
            return
        # upgrade()  # Commented out since Flask-Migrate is not installed
        print("INFO: Migrations skipped (Flask-Migrate not installed)")
    except Exception as e:
        print(f"ERROR: Error running migrations: {e}")

def main():
    """Main application entry point"""
    # Get configuration from environment
    environment = os.environ.get('FLASK_ENV', 'development').lower()
    config_name = {
        'production': 'ProductionConfig',
        'testing': 'TestingConfig',
        'development': 'DevelopmentConfig',
    }.get(environment, 'DevelopmentConfig')
    
    # Create Flask application
    app = create_app(config_name)
    
    with app.app_context():
        # Create tables for development
        if config_name == 'DevelopmentConfig':
            create_tables()
        else:
            # Run migrations for production
            run_migrations()
    
    # Get host and port from environment
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = config_name == 'DevelopmentConfig'
    
    print(f"🚀 Starting Hotel Booking System...")
    print(f"📊 Environment: {config_name}")
    print(f"🌐 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🐛 Debug: {debug}")
    print(f"📧 Mail Server: {app.config.get('MAIL_SERVER', 'Not configured')}")
    
    if config_name == 'DevelopmentConfig':
        print("\n📚 API Documentation: http://localhost:5000/api/docs")
        print("🔍 Admin Panel: http://localhost:5000/admin (admin role required)")
        print("📧 Mailpit: http://localhost:8025 (if running)")
    
    # Run the application
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )

if __name__ == '__main__':
    main()
