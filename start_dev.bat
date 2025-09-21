@echo off
echo ========================================
echo   Hotel Booking System - Windows Setup
echo ========================================
echo.

echo [1/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    pause
    exit /b 1
)

echo [2/5] Installing/updating dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo [3/5] Checking database connection...
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); print('✅ Database connected successfully!')"
if errorlevel 1 (
    echo ERROR: Database connection failed!
    echo Please check your PostgreSQL service and .env file
    pause
    exit /b 1
)

echo [4/5] Starting the application...
echo.
echo ========================================
echo   🚀 Starting Hotel Booking System
echo ========================================
echo.
echo 🌐 Application URL: http://localhost:5000
echo 📚 API Documentation: http://localhost:5000/api/docs
echo 🔍 Admin Panel: http://localhost:5000/admin
echo.
echo 📋 Sample Login Credentials:
echo   Admin: admin@namibiahotels.com / admin123
echo   Staff: staff@namibiahotels.com / staff123
echo   Guest: john.doe@example.com / password123
echo.
echo Press Ctrl+C to stop the application
echo ========================================
echo.

python run.py

echo.
echo Application stopped.
pause
