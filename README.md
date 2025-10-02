# Namibia Hotel Booking System

A comprehensive, production-grade hotel booking system built with Flask, SQLAlchemy, PostgreSQL, and Bootstrap. This system provides a complete solution for hotel reservations with advanced features including concurrency controls, payment processing, review systems, and administrative tools.

## Features

### Core Functionality
- **Hotel Management**: Complete CRUD operations for hotels, room types, and rooms
- **Booking System**: Advanced booking engine with real-time availability checking
- **Payment Processing**: Integrated Stripe payment system with webhook support
- **User Authentication**: JWT-based authentication with role-based access control
- **Review System**: Verified guest reviews with rating aggregation
- **Search & Discovery**: Advanced search with filters and availability checking

### Advanced Features
- **Overbooking Prevention**: Database-level concurrency controls with `FOR UPDATE` locks
- **Audit Logging**: Complete change tracking for security and compliance
- **Timezone Awareness**: Proper handling of dates and times for international bookings
- **Responsive Design**: Mobile-first Bootstrap interface with custom styling
- **API-First Architecture**: RESTful API with comprehensive documentation
- **Admin Dashboard**: Complete administrative interface with analytics

### Security Features
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Password Security**: bcrypt hashing with salt
- **Input Validation**: Comprehensive validation on all inputs
- **SQL Injection Prevention**: Parameterized queries only
- **Rate Limiting**: Protection against abuse and DoS attacks
- **Audit Trail**: Complete logging of all critical operations

## Architecture

### Technology Stack
- **Backend**: Flask 2.3+ with Python 3.9+
- **Database**: PostgreSQL 13+ with SQLAlchemy ORM
- **Authentication**: JWT with Flask-JWT-Extended
- **Frontend**: Bootstrap 5.3 with custom CSS and JavaScript
- **Payment**: Stripe integration with webhook support
- **Email**: Flask-Mail with Mailpit for development
- **Testing**: pytest with comprehensive test coverage

### Database Schema
The system uses a normalized database schema with the following key entities:
- **Users & Roles**: User management with role-based permissions
- **Hotels & Rooms**: Hotel and room type management
- **Bookings & Guests**: Reservation system with guest information
- **Payments**: Payment processing and transaction tracking
- **Reviews**: Guest review system with verification
- **Audit Logs**: Complete change tracking

##  Quick Start

### Prerequisites
- Python 3.9 or higher
- PostgreSQL 13 or higher
- Node.js (for frontend assets, optional)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/hotel-booking-system.git
   cd hotel-booking-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up PostgreSQL database**
   ```bash
   # Create database
   createdb hotel_booking_dev
   
   # Create user (optional)
   createuser -s hotel_user
   ```

6. **Initialize database**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

7. **Run the application**
   ```bash
   flask run
   ```

The application will be available at `http://localhost:5000`

### Development Setup

1. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Set up Mailpit for email testing**
   ```bash
   # Download and run Mailpit
   # Visit http://localhost:8025 for email interface
   ```

3. **Run tests**
   ```bash
   pytest tests/ -v
   ```

## Project Structure

```
hotel-booking-system/
├── app/                          # Main application package
│   ├── __init__.py              # Flask app factory
│   ├── models.py                # SQLAlchemy models
│   ├── routes/                  # API route blueprints
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── hotels.py           # Hotel management
│   │   ├── bookings.py         # Booking system
│   │   ├── payments.py         # Payment processing
│   │   ├── reviews.py          # Review system
│   │   ├── admin.py            # Admin endpoints
│   │   └── main.py             # Main web routes
│   └── templates/              # Jinja2 templates
│       ├── base.html           # Base template
│       ├── index.html          # Homepage
│       ├── search.html         # Search interface
│       └── ...                 # Other templates
├── tests/                       # Test suite
│   ├── test_models.py          # Model tests
│   ├── test_overbooking.py     # Concurrency tests
│   ├── test_api.py             # API endpoint tests
│   └── conftest.py             # Test configuration
├── docs/                        # Documentation
│   └── ER_DIAGRAM.md           # Database schema
├── migrations/                  # Database migrations
├── static/                      # Static assets
├── config.py                    # Configuration classes
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
├── .env.example                 # Environment variables template
├── API_DOCS.md                 # API documentation
├── SECURITY.md                 # Security checklist
└── README.md                   # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Flask Configuration
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/hotel_booking_dev
DEV_DATABASE_URL=postgresql://user:password@localhost/hotel_booking_dev
TEST_DATABASE_URL=postgresql://user:password@localhost/hotel_booking_test

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key

# Email Configuration (Mailpit for development)
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USE_TLS=False
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=noreply@hotelbooking.com

# Stripe Configuration (for production)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Application Settings
TIMEZONE=Africa/Windhoek
UPLOAD_FOLDER=uploads
```

### Database Configuration

The system supports multiple database configurations:

- **Development**: SQLite or PostgreSQL
- **Testing**: Separate test database
- **Production**: PostgreSQL with connection pooling

##  Testing

The project includes comprehensive testing with the following categories:

### Unit Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_models.py -v          # Model tests
pytest tests/test_overbooking.py -v     # Concurrency tests
pytest tests/test_api.py -v             # API tests
```

### Concurrency Testing
The system includes specialized tests for overbooking prevention:

```bash
# Run concurrency tests
pytest tests/test_overbooking.py::TestOverbookingPrevention::test_concurrent_bookings_same_room_type -v
```

### Test Coverage
```bash
# Generate coverage report
pytest --cov=app tests/
coverage html
```

## Deployment

### Production Deployment

1. **Set production environment variables**
   ```bash
   export FLASK_ENV=production
   export DATABASE_URL=postgresql://user:pass@host/db
   export JWT_SECRET_KEY=your-production-secret
   ```

2. **Install production dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run database migrations**
   ```bash
   flask db upgrade
   ```

4. **Start the application**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

```bash
# Build and run
docker build -t hotel-booking-system .
docker run -d -p 5000:5000 \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  -e JWT_SECRET_KEY=your-secret \
  hotel-booking-system
```

## API Documentation

The API provides comprehensive RESTful endpoints for all functionality. See [API_DOCS.md](API_DOCS.md) for complete documentation including:

- Authentication endpoints
- Hotel management
- Booking system
- Payment processing
- Review system
- Admin functions

### Quick API Examples

**Register a user:**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "username",
    "password": "password123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

**Search hotels:**
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "check_in": "2024-02-01",
    "check_out": "2024-02-03",
    "guests": 2,
    "city": "Windhoek"
  }'
```

**Create a booking:**
```bash
curl -X POST http://localhost:5000/api/bookings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "hotel_id": 1,
    "room_type_id": 1,
    "check_in_date": "2024-02-01",
    "check_out_date": "2024-02-03",
    "guests": [{
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com"
    }]
  }'
```

## 🔒 Security

The system implements comprehensive security measures:

### Authentication & Authorization
- JWT tokens with expiration
- Role-based access control
- Password hashing with bcrypt
- Session management

### Data Protection
- SQL injection prevention
- XSS protection
- CSRF protection
- Input validation and sanitization

### Operational Security
- Audit logging
- Rate limiting
- Error handling
- Secure headers

See [SECURITY.md](SECURITY.md) for the complete security checklist.

## Frontend

The frontend is built with Bootstrap 5.3 and includes:

### Design System
- **Colors**: Primary (#06043e), Secondary (#05eeff), Accent (#ec4f00)
- **Typography**: Playfair Display (headings), Lora (body)
- **Components**: Custom-styled Bootstrap components
- **Responsive**: Mobile-first design approach

### Key Pages
- **Homepage**: Featured hotels and search interface
- **Search**: Advanced hotel search with filters
- **Hotel Details**: Comprehensive hotel information
- **Booking Flow**: Step-by-step booking process
- **User Dashboard**: Profile and booking management
- **Admin Panel**: Administrative interface

## 🛠️ Development

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Comprehensive docstrings
- Consistent naming conventions

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add new feature"

# Push and create PR
git push origin feature/new-feature
```

### Database Migrations
```bash
# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade

# Rollback migration
flask db downgrade
```

## Monitoring & Analytics

### Admin Dashboard
The admin dashboard provides:
- Booking statistics and trends
- Revenue analytics
- User management
- System health monitoring
- Audit log viewing

### Logging
- Application logs with different levels
- Audit logs for security
- Error tracking
- Performance monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install

# Run linting
flake8 app/
black app/

# Run tests
pytest tests/ -v --cov=app
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- **Email**: support@namibiahotels.com
- **Documentation**: [API Documentation](API_DOCS.md)
- **Issues**: [GitHub Issues](https://github.com/your-username/hotel-booking-system/issues)

## Acknowledgments

- Flask community for the excellent framework
- Bootstrap team for the responsive framework
- PostgreSQL team for the robust database
- All contributors and testers

---

**Built with love in Namibia**
**University of Namibia - 2025**
