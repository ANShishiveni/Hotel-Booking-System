# Hotel Booking System

A professional, production-grade hotel booking system built with Flask, SQLAlchemy, PostgreSQL, and Docker. Features timezone-aware booking logic, concurrency controls, payment processing, and comprehensive security measures.

## 🏨 Features

- **Hotel Management**: Complete hotel and room type management
- **Booking System**: Timezone-aware booking with concurrency controls
- **Payment Processing**: Stripe integration with webhook support
- **User Management**: JWT authentication with role-based access control
- **Reviews & Ratings**: Guest review system with verification
- **Admin Dashboard**: Comprehensive admin interface with analytics
- **Security**: OWASP compliance with comprehensive security measures
- **API**: RESTful API with comprehensive documentation
- **Testing**: Unit tests including concurrency testing
- **Docker**: Complete containerization with docker-compose

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+ (for local development)
- Redis 7+ (for local development)

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/hotel-booking-system.git
   cd hotel-booking-system
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Start the application**
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

4. **Run database migrations**
   ```bash
   docker-compose -f docker/docker-compose.yml run --rm migrate
   ```

5. **Access the application**
   - API: http://localhost:5000
   - Health Check: http://localhost:5000/health
   - API Documentation: http://localhost:5000/api/docs

### Local Development

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. **Set up environment**
   ```bash
   cp env.example .env
   # Edit .env with your local configuration
   ```

3. **Set up database**
   ```bash
   # Start PostgreSQL and Redis
   # Create database
   createdb hotel_booking
   
   # Run migrations
   flask db upgrade
   ```

4. **Seed initial data**
   ```bash
   python scripts/seed_data.py
   ```

5. **Run the application**
   ```bash
   python -m flask run
   ```

## 🏗️ Architecture

### Technology Stack

- **Backend**: Flask 2.3+, Python 3.11+
- **Database**: PostgreSQL 15+ with SQLAlchemy ORM
- **Cache/Sessions**: Redis 7+
- **Authentication**: JWT with Flask-JWT-Extended
- **Payments**: Stripe API integration
- **Containerization**: Docker with multi-stage builds
- **Testing**: pytest with comprehensive test coverage
- **Documentation**: Markdown with API documentation

### Database Schema

The system uses a normalized database schema with the following main entities:

- **Users & Roles**: Authentication and authorization
- **Hotels**: Hotel information and room types
- **Bookings**: Reservation management with concurrency controls
- **Payments**: Payment processing and transaction tracking
- **Reviews**: Guest feedback and ratings
- **Audit Logs**: Complete audit trail for all operations

See [ER_DIAGRAM.md](ER_DIAGRAM.md) for the complete entity relationship diagram.

## 📚 API Documentation

### Authentication Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - User logout
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile

### Hotel Endpoints

- `GET /api/hotels` - List hotels with filtering
- `GET /api/hotels/{id}` - Get hotel details
- `GET /api/hotels/{id}/room-types` - Get hotel room types
- `POST /api/hotels` - Create hotel (admin)
- `PUT /api/hotels/{id}` - Update hotel (admin)

### Booking Endpoints

- `GET /api/bookings/search` - Search room availability
- `POST /api/bookings/create` - Create new booking
- `GET /api/bookings` - Get user bookings
- `GET /api/bookings/{id}` - Get booking details
- `POST /api/bookings/{id}/cancel` - Cancel booking
- `POST /api/bookings/{id}/checkin` - Check-in (admin)
- `POST /api/bookings/{id}/checkout` - Check-out (admin)

### Payment Endpoints

- `POST /api/payments/process` - Process payment
- `GET /api/payments/{id}` - Get payment details
- `POST /api/payments/{id}/refund` - Refund payment (admin)
- `GET /api/payments/methods` - Get payment methods
- `POST /api/payments/webhook/stripe` - Stripe webhook
- `POST /api/payments/webhook/paypal` - PayPal webhook

### Review Endpoints

- `GET /api/reviews` - Get reviews with filtering
- `GET /api/reviews/hotel/{id}` - Get hotel reviews
- `GET /api/reviews/{id}` - Get review details
- `POST /api/reviews` - Create review
- `PUT /api/reviews/{id}` - Update review
- `DELETE /api/reviews/{id}` - Delete review

### Admin Endpoints

- `GET /api/admin/dashboard` - Dashboard statistics
- `GET /api/admin/bookings` - All bookings (admin)
- `GET /api/admin/users` - All users (admin)
- `GET /api/admin/payments` - All payments (admin)
- `GET /api/admin/audit-logs` - Audit logs (admin)
- `GET /api/admin/reports/revenue` - Revenue report (admin)

See [docs/API_DOCS.md](docs/API_DOCS.md) for complete API documentation with examples.

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest tests/test_overbooking.py  # Concurrency tests
pytest tests/test_auth.py         # Authentication tests
pytest tests/test_booking.py      # Booking tests
pytest tests/test_payment.py      # Payment tests

# Run tests in parallel
pytest -n auto
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Concurrency Tests**: Overbooking prevention testing
- **Security Tests**: Authentication and authorization testing
- **Performance Tests**: Load and stress testing

## 🔒 Security

The system implements comprehensive security measures following OWASP guidelines:

### Security Features

- **Authentication**: JWT-based authentication with secure token management
- **Authorization**: Role-based access control (RBAC) with granular permissions
- **Data Protection**: Encryption at rest and in transit
- **Input Validation**: Comprehensive input validation and sanitization
- **Rate Limiting**: API rate limiting to prevent abuse
- **Audit Logging**: Complete audit trail for all operations
- **Security Headers**: Proper HTTP security headers
- **Dependency Security**: Regular security scanning and updates

### Security Compliance

- **OWASP Top 10**: Full compliance with OWASP security guidelines
- **PCI DSS**: Payment card industry compliance for payment processing
- **GDPR**: General data protection regulation compliance
- **Security Testing**: Automated security scanning and testing

See [docs/SECURITY.md](docs/SECURITY.md) for the complete security checklist and guidelines.

## 🐳 Docker Configuration

### Development Environment

```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.yml down
```

### Production Environment

```bash
# Start production environment
docker-compose -f docker/docker-compose.prod.yml up -d

# Scale web service
docker-compose -f docker/docker-compose.prod.yml up -d --scale web=3
```

### Services

- **Web Application**: Flask application with Gunicorn
- **Database**: PostgreSQL with persistent storage
- **Cache**: Redis for caching and rate limiting
- **Reverse Proxy**: Nginx for load balancing and SSL termination
- **Monitoring**: Prometheus and Grafana for metrics and monitoring

## 📊 Monitoring & Observability

### Health Checks

- **Application Health**: `/health` endpoint for application status
- **Database Health**: Database connection monitoring
- **Redis Health**: Cache connection monitoring
- **External Services**: Payment gateway connectivity

### Metrics & Monitoring

- **Application Metrics**: Request rates, response times, error rates
- **Business Metrics**: Booking rates, revenue, occupancy
- **Infrastructure Metrics**: CPU, memory, disk usage
- **Custom Metrics**: Payment success rates, user activity

### Logging

- **Structured Logging**: JSON-formatted logs for easy parsing
- **Log Levels**: Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- **Log Rotation**: Automatic log rotation to prevent disk space issues
- **Centralized Logging**: ELK stack integration for log aggregation

## 🚀 Deployment

### Environment Configuration

The application supports multiple environments:

- **Development**: Local development with debug mode
- **Testing**: Automated testing environment
- **Staging**: Pre-production testing environment
- **Production**: Live production environment

### Environment Variables

Key environment variables for configuration:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Redis
REDIS_URL=redis://:password@host:port/db

# Payments
STRIPE_SECRET_KEY=sk_live_your_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### Production Deployment

1. **Set up production environment**
   ```bash
   # Configure production environment variables
   cp env.example .env.production
   # Edit .env.production with production values
   ```

2. **Deploy with Docker**
   ```bash
   docker-compose -f docker/docker-compose.prod.yml up -d
   ```

3. **Run database migrations**
   ```bash
   docker-compose -f docker/docker-compose.prod.yml run --rm migrate
   ```

4. **Set up SSL certificates**
   ```bash
   # Place SSL certificates in docker/ssl/
   # Configure nginx for HTTPS
   ```

5. **Configure monitoring**
   ```bash
   # Set up Prometheus and Grafana
   # Configure alerting rules
   ```

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Set up development environment
4. Make your changes
5. Add tests for new features
6. Ensure all tests pass
7. Submit a pull request

### Code Style

- Follow PEP 8 style guidelines
- Use Black for code formatting
- Use isort for import sorting
- Add type hints where appropriate
- Write comprehensive docstrings

### Testing Requirements

- All new features must have tests
- Maintain or improve test coverage
- Include integration tests for API endpoints
- Add security tests for authentication/authorization

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation

- [API Documentation](docs/API_DOCS.md)
- [Security Guidelines](docs/SECURITY.md)
- [Database Schema](ER_DIAGRAM.md)
- [Project Structure](PROJECT_STRUCTURE.md)

### Getting Help

- Create an issue for bug reports
- Use discussions for questions
- Check existing issues and documentation
- Contact the maintainers for security issues

## 🎯 Roadmap

### Upcoming Features

- [ ] Mobile app API endpoints
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Advanced search and filtering
- [ ] Integration with external booking systems
- [ ] Machine learning for pricing optimization
- [ ] Advanced reporting and business intelligence

### Performance Improvements

- [ ] Database query optimization
- [ ] Caching improvements
- [ ] API response compression
- [ ] CDN integration
- [ ] Database read replicas

---

**Built with ❤️ using Flask, PostgreSQL, and modern web technologies.**
