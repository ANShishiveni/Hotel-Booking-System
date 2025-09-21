@echo off
echo ========================================
echo   Hotel Booking System - Windows Setup
echo ========================================
echo.

echo This script will set up the Hotel Booking System on Windows.
echo Make sure you have Python 3.9+ and PostgreSQL installed.
echo.
pause

echo [1/6] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment!
    echo Please make sure Python is installed and in PATH.
    pause
    exit /b 1
)

echo [2/6] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/6] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo [4/6] Setting up environment file...
if not exist .env (
    copy env.example .env
    echo ✅ Created .env file from template
    echo.
    echo ⚠️  IMPORTANT: Please edit the .env file with your database settings:
    echo    - Update DATABASE_URL with your PostgreSQL credentials
    echo    - Change SECRET_KEY and JWT_SECRET_KEY for security
    echo.
    echo Opening .env file for editing...
    notepad .env
    echo.
    echo Press any key after you've saved the .env file...
    pause
) else (
    echo ✅ .env file already exists
)

echo [5/6] Testing database connection...
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); print('✅ Database connected successfully!')"
if errorlevel 1 (
    echo.
    echo ❌ Database connection failed!
    echo.
    echo Please check:
    echo 1. PostgreSQL service is running
    echo 2. Database 'hotel_booking_dev' exists
    echo 3. User 'hotel_user' with password 'hotel_pass' exists
    echo 4. Your .env file has correct DATABASE_URL
    echo.
    echo You can create the database and user using:
    echo psql -U postgres
    echo CREATE DATABASE hotel_booking_dev;
    echo CREATE USER hotel_user WITH PASSWORD 'hotel_pass';
    echo GRANT ALL PRIVILEGES ON DATABASE hotel_booking_dev TO hotel_user;
    echo \q
    echo.
    pause
    exit /b 1
)

echo [6/6] Initializing database with sample data...
python init_db.py
if errorlevel 1 (
    echo ERROR: Failed to initialize database!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✅ Setup Completed Successfully!
echo ========================================
echo.
echo 🎉 Your Hotel Booking System is ready!
echo.
echo To start the application, run: start_dev.bat
echo Or manually: python run.py
echo.
echo 🌐 Application will be available at: http://localhost:5000
echo.
echo 📋 Sample Login Credentials:
echo   Admin: admin@namibiahotels.com / admin123
echo   Staff: staff@namibiahotels.com / staff123
echo   Guest: john.doe@example.com / password123
echo.
echo Press any key to exit...
pause
