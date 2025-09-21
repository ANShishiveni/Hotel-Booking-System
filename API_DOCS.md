# Hotel Booking System API Documentation

## Overview

The Hotel Booking System API provides comprehensive endpoints for managing hotels, bookings, payments, reviews, and user authentication. The API follows RESTful principles and uses JWT authentication.

## Base URL

```
http://localhost:5000/api
```

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Error Handling

All API responses follow a consistent format:

### Success Response
```json
{
    "message": "Success message",
    "data": { ... }
}
```

### Error Response
```json
{
    "error": "Error description",
    "details": { ... }
}
```

## Endpoints

### Authentication

#### Register User
```http
POST /auth/register
```

**Request Body:**
```json
{
    "email": "user@example.com",
    "username": "username",
    "password": "password123",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+264123456789"
}
```

**Response:**
```json
{
    "message": "User registered successfully",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "username": "username",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+264123456789",
        "is_active": true,
        "email_verified": false,
        "created_at": "2024-01-01T00:00:00",
        "roles": ["guest"]
    }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "username",
    "password": "password123",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+264123456789"
  }'
```

#### Login User
```http
POST /auth/login
```

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "password123"
}
```

**Response:**
```json
{
    "message": "Login successful",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "username": "username",
        "first_name": "John",
        "last_name": "Doe",
        "roles": ["guest"]
    }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

#### Get User Profile
```http
GET /auth/profile
Authorization: Bearer <token>
```

**Response:**
```json
{
    "user": {
        "id": 1,
        "email": "user@example.com",
        "username": "username",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+264123456789",
        "is_active": true,
        "email_verified": false,
        "created_at": "2024-01-01T00:00:00",
        "roles": ["guest"]
    }
}
```

**cURL Example:**
```bash
curl -X GET http://localhost:5000/api/auth/profile \
  -H "Authorization: Bearer <your_token>"
```

#### Refresh Token
```http
POST /auth/refresh
Authorization: Bearer <refresh_token>
```

**Response:**
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Logout
```http
POST /auth/logout
Authorization: Bearer <token>
```

**Response:**
```json
{
    "message": "Successfully logged out"
}
```

### Hotels

#### Get All Hotels
```http
GET /hotels?page=1&per_page=12&city=Windhoek&star_rating=4&search=hotel
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 12)
- `city` (optional): Filter by city
- `star_rating` (optional): Minimum star rating
- `search` (optional): Search in name, description, city

**Response:**
```json
{
    "hotels": [
        {
            "id": 1,
            "name": "Namibia Luxury Hotel",
            "description": "Premium hotel in Windhoek",
            "address": "123 Independence Ave",
            "city": "Windhoek",
            "country": "Namibia",
            "star_rating": 5,
            "amenities": ["WiFi", "Pool", "Restaurant"],
            "images": ["hotel1.jpg", "hotel2.jpg"],
            "is_active": true,
            "created_at": "2024-01-01T00:00:00",
            "average_rating": 4.5,
            "room_types_count": 3
        }
    ],
    "pagination": {
        "page": 1,
        "per_page": 12,
        "total": 25,
        "pages": 3,
        "has_next": true,
        "has_prev": false
    }
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:5000/api/hotels?city=Windhoek&star_rating=4" \
  -H "Content-Type: application/json"
```

#### Get Hotel Details
```http
GET /hotels/{hotel_id}
```

**Response:**
```json
{
    "hotel": {
        "id": 1,
        "name": "Namibia Luxury Hotel",
        "description": "Premium hotel in Windhoek",
        "address": "123 Independence Ave",
        "city": "Windhoek",
        "country": "Namibia",
        "star_rating": 5,
        "amenities": ["WiFi", "Pool", "Restaurant"],
        "images": ["hotel1.jpg", "hotel2.jpg"],
        "policies": {
            "check_in": "14:00",
            "check_out": "11:00",
            "cancellation": "Free cancellation up to 24 hours"
        },
        "is_active": true,
        "average_rating": 4.5
    }
}
```

#### Get Hotel Room Types
```http
GET /hotels/{hotel_id}/room-types
```

**Response:**
```json
{
    "hotel": { ... },
    "room_types": [
        {
            "id": 1,
            "hotel_id": 1,
            "name": "Standard Room",
            "description": "Comfortable standard room",
            "base_price": 150.00,
            "max_occupancy": 2,
            "bed_type": "Queen",
            "room_size": 25,
            "amenities": ["WiFi", "TV", "Mini-bar"],
            "images": ["room1.jpg"],
            "is_active": true,
            "available_rooms": 5
        }
    ]
}
```

#### Search Hotels with Availability
```http
POST /search
```

**Request Body:**
```json
{
    "check_in": "2024-02-01",
    "check_out": "2024-02-03",
    "guests": 2,
    "city": "Windhoek"
}
```

**Response:**
```json
{
    "hotels": [
        {
            "id": 1,
            "name": "Namibia Luxury Hotel",
            "city": "Windhoek",
            "available_room_types": [
                {
                    "id": 1,
                    "name": "Standard Room",
                    "base_price": 150.00,
                    "available_rooms": 3,
                    "max_occupancy": 2
                }
            ]
        }
    ],
    "search_params": {
        "check_in": "2024-02-01",
        "check_out": "2024-02-03",
        "guests": 2,
        "city": "Windhoek"
    }
}
```

**cURL Example:**
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

### Bookings

#### Get User Bookings
```http
GET /bookings?page=1&per_page=10&status=confirmed
Authorization: Bearer <token>
```

**Query Parameters:**
- `page` (optional): Page number
- `per_page` (optional): Items per page
- `status` (optional): Filter by booking status

**Response:**
```json
{
    "bookings": [
        {
            "id": 1,
            "booking_reference": "BK12345678",
            "user_id": 1,
            "hotel_id": 1,
            "room_id": 1,
            "check_in_date": "2024-02-01",
            "check_out_date": "2024-02-03",
            "nights": 2,
            "adults": 2,
            "children": 0,
            "total_amount": 300.00,
            "status": "confirmed",
            "created_at": "2024-01-15T10:00:00",
            "hotel": {
                "id": 1,
                "name": "Namibia Luxury Hotel",
                "city": "Windhoek"
            },
            "room": {
                "id": 1,
                "room_number": "101",
                "floor": 1
            },
            "guests": [
                {
                    "id": 1,
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@example.com",
                    "is_primary_guest": true
                }
            ]
        }
    ],
    "pagination": {
        "page": 1,
        "per_page": 10,
        "total": 5,
        "pages": 1,
        "has_next": false,
        "has_prev": false
    }
}
```

#### Create Booking
```http
POST /bookings
Authorization: Bearer <token>
```

**Request Body:**
```json
{
    "hotel_id": 1,
    "room_type_id": 1,
    "check_in_date": "2024-02-01",
    "check_out_date": "2024-02-03",
    "guests": [
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+264123456789",
            "date_of_birth": "1990-01-01",
            "nationality": "Namibian",
            "id_number": "90010112345"
        }
    ],
    "special_requests": "Ground floor room preferred"
}
```

**Response:**
```json
{
    "message": "Booking created successfully",
    "booking": {
        "id": 1,
        "booking_reference": "BK12345678",
        "user_id": 1,
        "hotel_id": 1,
        "room_id": 1,
        "check_in_date": "2024-02-01",
        "check_out_date": "2024-02-03",
        "nights": 2,
        "adults": 2,
        "children": 0,
        "total_amount": 300.00,
        "status": "pending",
        "created_at": "2024-01-15T10:00:00"
    }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/bookings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "hotel_id": 1,
    "room_type_id": 1,
    "check_in_date": "2024-02-01",
    "check_out_date": "2024-02-03",
    "guests": [
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+264123456789"
        }
    ]
  }'
```

#### Get Booking Details
```http
GET /bookings/{booking_id}
Authorization: Bearer <token>
```

#### Confirm Booking
```http
POST /bookings/{booking_id}/confirm
Authorization: Bearer <token>
```

**Response:**
```json
{
    "message": "Booking confirmed successfully",
    "booking": {
        "id": 1,
        "status": "confirmed",
        "confirmed_at": "2024-01-15T10:30:00"
    }
}
```

#### Cancel Booking
```http
POST /bookings/{booking_id}/cancel
Authorization: Bearer <token>
```

**Request Body:**
```json
{
    "reason": "Change of plans"
}
```

**Response:**
```json
{
    "message": "Booking cancelled successfully",
    "booking": {
        "id": 1,
        "status": "cancelled",
        "cancelled_at": "2024-01-15T11:00:00"
    },
    "cancellation_details": {
        "cancellation_fee": 75.00,
        "refund_amount": 225.00,
        "days_until_checkin": 17
    }
}
```

#### Check Availability
```http
POST /bookings/availability
```

**Request Body:**
```json
{
    "hotel_id": 1,
    "room_type_id": 1,
    "check_in_date": "2024-02-01",
    "check_out_date": "2024-02-03"
}
```

**Response:**
```json
{
    "available": true,
    "available_rooms": 3,
    "room_type": {
        "id": 1,
        "name": "Standard Room",
        "base_price": 150.00
    }
}
```

### Payments

#### Create Payment Intent
```http
POST /payments/create-payment-intent
Authorization: Bearer <token>
```

**Request Body:**
```json
{
    "booking_id": 1
}
```

**Response:**
```json
{
    "payment_intent": {
        "id": "pi_mock_123",
        "client_secret": "pi_mock_123_secret",
        "amount": 30000,
        "currency": "nad",
        "status": "requires_payment_method"
    },
    "payment": {
        "id": 1,
        "booking_id": 1,
        "payment_reference": "PAY1234567890",
        "amount": 300.00,
        "currency": "NAD",
        "payment_method": "card",
        "payment_provider": "stripe",
        "status": "pending"
    }
}
```

#### Confirm Payment
```http
POST /payments/confirm-payment
Authorization: Bearer <token>
```

**Request Body:**
```json
{
    "payment_intent_id": "pi_mock_123"
}
```

**Response:**
```json
{
    "message": "Payment confirmed successfully",
    "payment": {
        "id": 1,
        "status": "completed",
        "processed_at": "2024-01-15T12:00:00"
    },
    "booking": {
        "id": 1,
        "status": "confirmed"
    }
}
```

#### Get Payment Details
```http
GET /payments/{payment_id}
Authorization: Bearer <token>
```

#### Get Booking Payments
```http
GET /payments/booking/{booking_id}
Authorization: Bearer <token>
```

#### Get Payment Methods
```http
GET /payments/methods
```

**Response:**
```json
{
    "payment_methods": [
        {
            "id": "card",
            "name": "Credit/Debit Card",
            "provider": "stripe",
            "enabled": true,
            "currencies": ["NAD", "USD", "EUR"]
        },
        {
            "id": "bank_transfer",
            "name": "Bank Transfer",
            "provider": "manual",
            "enabled": true,
            "currencies": ["NAD"]
        }
    ]
}
```

### Reviews

#### Get Reviews
```http
GET /reviews?page=1&per_page=10&hotel_id=1&rating=5&verified_only=true
```

**Query Parameters:**
- `page` (optional): Page number
- `per_page` (optional): Items per page
- `hotel_id` (optional): Filter by hotel
- `rating` (optional): Filter by rating
- `verified_only` (optional): Only verified reviews

**Response:**
```json
{
    "reviews": [
        {
            "id": 1,
            "hotel_id": 1,
            "user_id": 1,
            "booking_id": 1,
            "rating": 5,
            "title": "Excellent stay!",
            "comment": "Amazing hotel with great service",
            "is_verified": true,
            "is_active": true,
            "created_at": "2024-01-20T15:00:00",
            "user": {
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe"
            }
        }
    ],
    "pagination": {
        "page": 1,
        "per_page": 10,
        "total": 25,
        "pages": 3,
        "has_next": true,
        "has_prev": false
    }
}
```

#### Create Review
```http
POST /reviews
Authorization: Bearer <token>
```

**Request Body:**
```json
{
    "hotel_id": 1,
    "booking_id": 1,
    "rating": 5,
    "title": "Excellent stay!",
    "comment": "Amazing hotel with great service and beautiful rooms."
}
```

**Response:**
```json
{
    "message": "Review created successfully",
    "review": {
        "id": 1,
        "hotel_id": 1,
        "user_id": 1,
        "booking_id": 1,
        "rating": 5,
        "title": "Excellent stay!",
        "comment": "Amazing hotel with great service and beautiful rooms.",
        "is_verified": true,
        "created_at": "2024-01-20T15:00:00"
    }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/reviews \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "hotel_id": 1,
    "booking_id": 1,
    "rating": 5,
    "title": "Excellent stay!",
    "comment": "Amazing hotel with great service."
  }'
```

#### Update Review
```http
PUT /reviews/{review_id}
Authorization: Bearer <token>
```

#### Delete Review
```http
DELETE /reviews/{review_id}
Authorization: Bearer <token>
```

#### Get Hotel Review Statistics
```http
GET /reviews/hotel/{hotel_id}/stats
```

**Response:**
```json
{
    "hotel": {
        "id": 1,
        "name": "Namibia Luxury Hotel"
    },
    "statistics": {
        "total_reviews": 25,
        "average_rating": 4.2,
        "min_rating": 1,
        "max_rating": 5,
        "rating_distribution": {
            "1": 1,
            "2": 2,
            "3": 5,
            "4": 8,
            "5": 9
        }
    },
    "recent_reviews": [
        {
            "id": 1,
            "rating": 5,
            "title": "Excellent stay!",
            "comment": "Amazing hotel",
            "created_at": "2024-01-20T15:00:00",
            "user": {
                "first_name": "John",
                "last_name": "Doe"
            }
        }
    ]
}
```

### Admin Endpoints

#### Get Admin Dashboard
```http
GET /admin/dashboard?days=30
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
    "statistics": {
        "total_hotels": 15,
        "total_users": 150,
        "total_bookings": 500,
        "total_revenue": 75000.00,
        "pending_bookings": 25,
        "active_reviews": 200
    },
    "revenue_by_month": [
        {
            "month": "2024-01",
            "revenue": 25000.00
        }
    ],
    "bookings_by_status": [
        {
            "status": "confirmed",
            "count": 400
        },
        {
            "status": "pending",
            "count": 25
        }
    ],
    "top_hotels": [
        {
            "hotel_id": 1,
            "name": "Namibia Luxury Hotel",
            "booking_count": 150
        }
    ],
    "recent_activities": [
        {
            "id": 1,
            "table_name": "bookings",
            "record_id": 1,
            "action": "CREATE",
            "user_id": 1,
            "created_at": "2024-01-15T10:00:00"
        }
    ]
}
```

#### Get All Users
```http
GET /admin/users?page=1&per_page=20&search=john&role=guest
Authorization: Bearer <admin_token>
```

#### Update User Roles
```http
PUT /admin/users/{user_id}/roles
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
    "roles": ["guest", "staff"]
}
```

#### Get All Bookings
```http
GET /admin/bookings?page=1&status=confirmed&hotel_id=1
Authorization: Bearer <admin_token>
```

#### Export Bookings
```http
GET /admin/bookings/export?status=confirmed&start_date=2024-01-01
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
    "csv_data": "Booking ID,Reference,Hotel,Room,Guest,Email,Check In,Check Out,Nights,Adults,Children,Total Amount,Status,Created At\n1,BK12345678,Namibia Luxury Hotel,101,John Doe,john@example.com,2024-02-01,2024-02-03,2,2,0,300.00,confirmed,2024-01-15T10:00:00",
    "filename": "bookings_export_20240115_120000.csv",
    "record_count": 1
}
```

#### Get All Payments
```http
GET /admin/payments?page=1&status=completed
Authorization: Bearer <admin_token>
```

#### Get Audit Logs
```http
GET /admin/audit-logs?page=1&table_name=bookings&action=CREATE
Authorization: Bearer <admin_token>
```

#### Get System Settings
```http
GET /admin/system-settings
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
    "settings": {
        "booking_cancellation_policy": {
            "same_day_fee": 1.0,
            "one_two_days_fee": 0.5,
            "three_six_days_fee": 0.25,
            "seven_plus_days_fee": 0.0
        },
        "payment_settings": {
            "default_currency": "NAD",
            "tax_rate": 0.15,
            "supported_currencies": ["NAD", "USD", "EUR"]
        },
        "email_settings": {
            "booking_confirmation": true,
            "payment_confirmation": true,
            "cancellation_notification": true
        }
    }
}
```

## Webhooks

### Stripe Payment Webhook
```http
POST /payments/webhook
```

This endpoint handles Stripe webhook events for payment processing. It expects a Stripe signature header and processes events like:
- `payment_intent.succeeded`
- `payment_intent.payment_failed`

**Headers:**
```
Stripe-Signature: <stripe_signature>
Content-Type: application/json
```

## Rate Limiting

The API implements rate limiting to prevent abuse:
- Authentication endpoints: 5 requests per minute per IP
- General API endpoints: 100 requests per minute per user
- Search endpoints: 20 requests per minute per user

## Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `409` - Conflict
- `422` - Unprocessable Entity
- `429` - Too Many Requests
- `500` - Internal Server Error

## Data Models

### User
```json
{
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+264123456789",
    "is_active": true,
    "email_verified": false,
    "created_at": "2024-01-01T00:00:00",
    "roles": ["guest"]
}
```

### Hotel
```json
{
    "id": 1,
    "name": "Namibia Luxury Hotel",
    "description": "Premium hotel in Windhoek",
    "address": "123 Independence Ave",
    "city": "Windhoek",
    "country": "Namibia",
    "star_rating": 5,
    "amenities": ["WiFi", "Pool", "Restaurant"],
    "images": ["hotel1.jpg", "hotel2.jpg"],
    "policies": {
        "check_in": "14:00",
        "check_out": "11:00"
    },
    "is_active": true,
    "average_rating": 4.5
}
```

### Booking
```json
{
    "id": 1,
    "booking_reference": "BK12345678",
    "user_id": 1,
    "hotel_id": 1,
    "room_id": 1,
    "check_in_date": "2024-02-01",
    "check_out_date": "2024-02-03",
    "nights": 2,
    "adults": 2,
    "children": 0,
    "total_amount": 300.00,
    "status": "confirmed",
    "created_at": "2024-01-15T10:00:00"
}
```

## Testing

The API includes comprehensive test coverage including:

### Unit Tests
- Model validation and relationships
- Business logic functions
- Data serialization

### Integration Tests
- API endpoint functionality
- Authentication flows
- Database transactions

### Concurrency Tests
- Overbooking prevention
- Race condition handling
- Database locking mechanisms

Run tests with:
```bash
pytest tests/ -v
```

Run specific test categories:
```bash
# Model tests
pytest tests/test_models.py -v

# Overbooking prevention tests
pytest tests/test_overbooking.py -v

# API tests
pytest tests/test_api.py -v
```

## Security Considerations

1. **JWT Tokens**: Short-lived access tokens with refresh tokens
2. **Password Hashing**: bcrypt with salt
3. **Input Validation**: Comprehensive validation on all inputs
4. **SQL Injection**: Parameterized queries only
5. **Rate Limiting**: Prevents abuse and DoS attacks
6. **CORS**: Configured for specific origins
7. **HTTPS**: Required in production
8. **Audit Logging**: All critical actions are logged
9. **Role-based Access**: Granular permissions system
10. **Data Encryption**: Sensitive data encrypted at rest

## Deployment

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/hotel_booking

# JWT
JWT_SECRET_KEY=your-secret-key

# Mail
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USERNAME=
MAIL_PASSWORD=

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# App
SECRET_KEY=your-app-secret-key
FLASK_ENV=production
```

### Docker Deployment
```bash
# Build image
docker build -t hotel-booking-system .

# Run container
docker run -d -p 5000:5000 \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  -e JWT_SECRET_KEY=your-secret \
  hotel-booking-system
```

### Database Migration
```bash
# Initialize migrations
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

## Support

For API support and questions:
- Email: api-support@namibiahotels.com
- Documentation: https://api.namibiahotels.com/docs
- Status Page: https://status.namibiahotels.com
