# Windows Local Setup Guide - Hotel Booking System

This guide will help you set up and run the Hotel Booking System locally on Windows without Docker.

## 📋 Prerequisites

### 1. Install Python 3.9 or higher
- Download from: https://www.python.org/downloads/
- **Important**: Check "Add Python to PATH" during installation
- Verify installation:
```cmd
python --version
pip --version
```

### 2. Install PostgreSQL
- Download from: https://www.postgresql.org/download/windows/
- During installation, remember the password you set for the `postgres` user
- Default port is 5432
- Install pgAdmin (optional but helpful for database management)

### 3. Install Git (optional)
- Download from: https://git-scm.com/download/win

## 🚀 Step-by-Step Setup

### Step 1: Navigate to Project Directory
Open Command Prompt or PowerShell and navigate to your project:
```cmd
cd C:\Users\Absalom\Documents\GitHub\Hotel-Booking-System
```

### Step 2: Create Virtual Environment
```cmd
python -m venv venv
```

### Step 3: Activate Virtual Environment
```cmd
venv\Scripts\activate
```
You should see `(venv)` at the beginning of your command prompt.

### Step 4: Install Dependencies
```cmd
pip install -r requirements.txt
```

### Step 5: Set Up Database

#### 5.1 Create Database and User
Open pgAdmin or use psql command line:

**Option A: Using pgAdmin (GUI)**
1. Open pgAdmin
2. Connect to PostgreSQL server
3. Right-click "Databases" → "Create" → "Database"
4. Name: `hotel_booking_dev`
5. Right-click "Login/Group Roles" → "Create" → "Login/Group Role"
6. Name: `hotel_user`, Password: `hotel_pass`
7. Grant database privileges

**Option B: Using psql (Command Line)**
```cmd
psql -U postgres
```
Then run these SQL commands:
```sql
CREATE DATABASE hotel_booking_dev;
CREATE USER hotel_user WITH PASSWORD 'hotel_pass';
GRANT ALL PRIVILEGES ON DATABASE hotel_booking_dev TO hotel_user;
\q
```

### Step 6: Configure Environment Variables
```cmd
copy env.example .env
```

Edit the `.env` file with your database settings:
```env
# Flask Configuration
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-in-production

# Database Configuration
DATABASE_URL=postgresql://hotel_user:hotel_pass@localhost:5432/hotel_booking_dev
DEV_DATABASE_URL=postgresql://hotel_user:hotel_pass@localhost:5432/hotel_booking_dev

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-change-in-production

# Email Configuration (Mailpit for development)
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USE_TLS=false
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=noreply@hotelbooking.com

# Application Settings
TIMEZONE=Africa/Windhoek
```

### Step 7: Initialize Database
```cmd
python init_db.py
```
This will create all tables and populate with sample data.

### Step 8: Run the Application
```cmd
python run.py
```

The application will start at: http://localhost:5000

## 🎯 Quick Test

### 1. Open Browser
Go to: http://localhost:5000

### 2. Test Login
- **Admin**: admin@namibiahotels.com / admin123
- **Staff**: staff@namibiahotels.com / staff123
- **Guest**: john.doe@example.com / password123

### 3. Test Features
- Browse hotels
- Search for availability
- Create a booking (requires login)
- View admin panel (admin account)

## 🔧 Troubleshooting

### Common Issues

#### 1. "psycopg2" Installation Error
If you get errors installing psycopg2:
```cmd
pip install psycopg2-binary
```

#### 2. Database Connection Error
Check your PostgreSQL service is running:
```cmd
services.msc
```
Look for "postgresql" service and ensure it's running.

#### 3. Port 5000 Already in Use
If port 5000 is busy, you can change it in `run.py` or set environment variable:
```cmd
set PORT=5001
python run.py
```

#### 4. Virtual Environment Issues
If activation doesn't work:
```cmd
venv\Scripts\activate.bat
```

#### 5. Permission Errors
Run Command Prompt as Administrator if you encounter permission issues.

### Database Connection Test
Test your database connection:
```cmd
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); print('Database connected successfully!')"
```

## 📧 Optional: Email Testing with Mailpit

### Install Mailpit
1. Download from: https://github.com/axllent/mailpit/releases
2. Extract and run: `mailpit.exe`
3. Access at: http://localhost:8025

### Configure in .env
```env
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USE_TLS=false
```

## 🧪 Running Tests

### Install Development Dependencies
```cmd
pip install -r requirements-dev.txt
```

### Run Tests
```cmd
pytest tests/ -v
```

### Run Specific Tests
```cmd
# Model tests
pytest tests/test_models.py -v

# Concurrency tests
pytest tests/test_overbooking.py -v
```

## 🔄 Daily Development Workflow

### Start Development Session
```cmd
cd C:\Users\Absalom\Documents\GitHub\Hotel-Booking-System
venv\Scripts\activate
python run.py
```

### Stop Application
Press `Ctrl+C` in the terminal

### Deactivate Virtual Environment
```cmd
deactivate
```

## 📁 Project Structure Reminder

```
Hotel-Booking-System/
├── app/                    # Main Flask application
├── tests/                  # Test suite
├── docs/                   # Documentation
├── venv/                   # Virtual environment (created)
├── .env                    # Environment variables (created)
├── run.py                  # Application entry point
└── init_db.py             # Database initialization
```

## 🎉 Success Indicators

You'll know everything is working when:
- ✅ Application starts without errors
- ✅ Browser shows the homepage at http://localhost:5000
- ✅ You can login with sample accounts
- ✅ Database tables are created
- ✅ You can search for hotels
- ✅ Admin panel is accessible

## 🆘 Getting Help

If you encounter issues:
1. Check the error messages in the terminal
2. Verify all prerequisites are installed
3. Ensure PostgreSQL is running
4. Check your .env file configuration
5. Try running the database connection test

## 🚀 Next Steps

Once everything is running:
1. Explore the admin panel
2. Create test bookings
3. Test the payment system
4. Review the API documentation
5. Run the test suite
6. Customize the hotel data

Happy coding! 🏨✨
