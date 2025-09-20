# Hotel Booking System API Documentation

## Overview

The Hotel Booking System provides a comprehensive REST API for managing hotels, bookings, payments, and reviews. The API is built with Flask and follows RESTful principles.

## Base URL

```
Development: http://localhost:5000/api
Production: https://your-domain.com/api
```

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Rate Limiting

- **General endpoints**: 200 requests per day, 50 per hour
- **Authentication endpoints**: 10 requests per minute
- **Booking endpoints**: 5 requests per minute
- **Search endpoints**: 30 requests per minute

## Error Responses

All error responses follow this format:

```json
{
  "error": "Error message description"
}
```

Common HTTP status codes:
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

---

## Authentication Endpoints

### Register User

**POST** `/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "role": "customer",
    "is_active": true,
    "created_at": "2023-01-01T00:00:00Z"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890"
  }'
```

### Login

**POST** `/auth/login`

Authenticate user and receive JWT tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "customer"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

### Refresh Token

**POST** `/auth/refresh`

Refresh access token using refresh token.

**Headers:**
```
Authorization: Bearer <refresh_token>
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Logout

**POST** `/auth/logout`

Logout user and invalidate tokens.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Logout successful"
}
```

### Get Profile

**GET** `/auth/profile`

Get current user profile information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "role": "customer",
    "role_permissions": ["book_room", "view_bookings", "write_reviews"],
    "is_active": true,
    "created_at": "2023-01-01T00:00:00Z"
  }
}
```

---

## Hotel Endpoints

### Get Hotels

**GET** `/hotels`

Get list of hotels with optional filtering.

**Query Parameters:**
- `city` (string) - Filter by city
- `country` (string) - Filter by country
- `limit` (integer) - Number of results (default: 20, max: 100)
- `offset` (integer) - Number of results to skip (default: 0)

**Response:**
```json
{
  "hotels": [
    {
      "id": 1,
      "name": "Grand Hotel",
      "address": "123 Main Street",
      "city": "New York",
      "state": "NY",
      "country": "USA",
      "postal_code": "10001",
      "phone": "+1234567890",
      "email": "info@grandhotel.com",
      "latitude": 40.7128,
      "longitude": -74.0060,
      "amenities": ["wifi", "parking", "pool"],
      "is_active": true
    }
  ],
  "pagination": {
    "total": 1,
    "limit": 20,
    "offset": 0,
    "has_more": false
  }
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:5000/api/hotels?city=New%20York&limit=10" \
  -H "Authorization: Bearer <access_token>"
```

### Get Hotel Details

**GET** `/hotels/{hotel_id}`

Get detailed information about a specific hotel.

**Response:**
```json
{
  "hotel": {
    "id": 1,
    "name": "Grand Hotel",
    "address": "123 Main Street",
    "city": "New York",
    "state": "NY",
    "country": "USA",
    "amenities": ["wifi", "parking", "pool"],
    "room_types": [
      {
        "id": 1,
        "name": "Standard Room",
        "description": "Comfortable standard room",
        "max_occupancy": 2,
        "amenities": ["wifi", "tv"],
        "base_price": 100.00,
        "pricing_rules": {"weekend_multiplier": 1.2}
      }
    ]
  }
}
```

### Get Hotel Room Types

**GET** `/hotels/{hotel_id}/room-types`

Get room types available for a specific hotel.

**Response:**
```json
{
  "hotel_id": 1,
  "hotel_name": "Grand Hotel",
  "room_types": [
    {
      "id": 1,
      "name": "Standard Room",
      "description": "Comfortable standard room",
      "max_occupancy": 2,
      "amenities": ["wifi", "tv"],
      "base_price": 100.00
    }
  ]
}
```

---

## Booking Endpoints

### Search Availability

**GET** `/bookings/search`

Search for available rooms.

**Query Parameters:**
- `hotel_id` (integer, required) - Hotel ID
- `check_in` (string, required) - Check-in date (YYYY-MM-DD)
- `check_out` (string, required) - Check-out date (YYYY-MM-DD)
- `adults` (integer) - Number of adults (default: 1)
- `children` (integer) - Number of children (default: 0)

**Response:**
```json
{
  "search_results": [
    {
      "room_type_id": 1,
      "name": "Standard Room",
      "description": "Comfortable standard room",
      "max_occupancy": 2,
      "amenities": ["wifi", "tv"],
      "rate_per_night": 100.00,
      "total_nights": 3,
      "total_amount": 300.00,
      "available_rooms": 5
    }
  ],
  "search_params": {
    "hotel_id": 1,
    "check_in": "2023-02-01",
    "check_out": "2023-02-04",
    "adults": 2,
    "children": 0
  }
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:5000/api/bookings/search?hotel_id=1&check_in=2023-02-01&check_out=2023-02-04&adults=2" \
  -H "Authorization: Bearer <access_token>"
```

### Create Booking

**POST** `/bookings/create`

Create a new booking.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "hotel_id": 1,
  "check_in": "2023-02-01",
  "check_out": "2023-02-04",
  "adults": 2,
  "children": 0,
  "room_selections": [
    {
      "room_type_id": 1,
      "quantity": 1
    }
  ],
  "guest_info": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "nationality": "US"
  },
  "special_requests": "Late checkout please"
}
```

**Response:**
```json
{
  "message": "Booking created successfully",
  "booking": {
    "id": 1,
    "booking_reference": "BK20230201001",
    "hotel_id": 1,
    "hotel_name": "Grand Hotel",
    "check_in": "2023-02-01T00:00:00Z",
    "check_out": "2023-02-04T00:00:00Z",
    "adults": 2,
    "children": 0,
    "total_amount": 300.00,
    "status": "confirmed",
    "duration_nights": 3,
    "can_cancel": true,
    "rooms": [
      {
        "id": 1,
        "room_number": "101",
        "room_type": "Standard Room",
        "rate": 100.00
      }
    ]
  }
}
```

### Get User Bookings

**GET** `/bookings`

Get bookings for the current user.

**Query Parameters:**
- `status` (string) - Filter by booking status
- `limit` (integer) - Number of results (default: 20)
- `offset` (integer) - Number of results to skip (default: 0)

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "bookings": [
    {
      "id": 1,
      "booking_reference": "BK20230201001",
      "hotel_name": "Grand Hotel",
      "check_in": "2023-02-01T00:00:00Z",
      "check_out": "2023-02-04T00:00:00Z",
      "total_amount": 300.00,
      "status": "confirmed",
      "can_cancel": true
    }
  ],
  "pagination": {
    "total": 1,
    "limit": 20,
    "offset": 0,
    "has_more": false
  }
}
```

### Get Booking Details

**GET** `/bookings/{booking_id}`

Get detailed information about a specific booking.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "booking": {
    "id": 1,
    "booking_reference": "BK20230201001",
    "hotel_name": "Grand Hotel",
    "guest_name": "John Doe",
    "check_in": "2023-02-01T00:00:00Z",
    "check_out": "2023-02-04T00:00:00Z",
    "total_amount": 300.00,
    "status": "confirmed",
    "rooms": [...],
    "payments": [...]
  }
}
```

### Cancel Booking

**POST** `/bookings/{booking_id}/cancel`

Cancel a booking.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
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
    "status": "cancelled"
  }
}
```

---

## Payment Endpoints

### Process Payment

**POST** `/payments/process`

Process payment for a booking.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "booking_id": 1,
  "payment_method": "stripe",
  "payment_data": {
    "payment_method_id": "pm_1234567890",
    "card_last4": "4242",
    "card_brand": "visa"
  }
}
```

**Response:**
```json
{
  "message": "Payment processed successfully",
  "payment": {
    "id": 1,
    "booking_id": 1,
    "booking_reference": "BK20230201001",
    "payment_method": "stripe",
    "amount": 300.00,
    "currency": "USD",
    "status": "completed",
    "transaction_id": "stripe_20230201123456_1",
    "is_successful": true,
    "processed_at": "2023-02-01T12:00:00Z"
  }
}
```

### Get Payment Details

**GET** `/payments/{payment_id}`

Get payment details.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "payment": {
    "id": 1,
    "booking_id": 1,
    "payment_method": "stripe",
    "amount": 300.00,
    "currency": "USD",
    "status": "completed",
    "transaction_id": "stripe_20230201123456_1",
    "processed_at": "2023-02-01T12:00:00Z"
  }
}
```

### Get Payment Methods

**GET** `/payments/methods`

Get available payment methods.

**Response:**
```json
{
  "payment_methods": [
    {
      "id": "stripe",
      "name": "Credit Card",
      "description": "Pay with Visa, MasterCard, American Express",
      "icon": "credit-card",
      "enabled": true
    },
    {
      "id": "paypal",
      "name": "PayPal",
      "description": "Pay with PayPal account",
      "icon": "paypal",
      "enabled": true
    }
  ]
}
```

---

## Review Endpoints

### Get Reviews

**GET** `/reviews`

Get reviews with filtering options.

**Query Parameters:**
- `hotel_id` (integer) - Filter by hotel
- `user_id` (integer) - Filter by user
- `rating` (integer) - Filter by rating (1-5)
- `verified_only` (boolean) - Only verified reviews
- `limit` (integer) - Number of results (default: 20)
- `offset` (integer) - Number of results to skip (default: 0)

**Response:**
```json
{
  "reviews": [
    {
      "id": 1,
      "booking_id": 1,
      "user_name": "John Doe",
      "rating": 5,
      "rating_stars": "★★★★★",
      "title": "Excellent stay!",
      "comment": "Great hotel, excellent service!",
      "is_verified": true,
      "can_be_edited": false,
      "created_at": "2023-02-05T00:00:00Z"
    }
  ],
  "pagination": {
    "total": 1,
    "limit": 20,
    "offset": 0,
    "has_more": false
  }
}
```

### Create Review

**POST** `/reviews`

Create a new review.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "booking_id": 1,
  "rating": 5,
  "title": "Excellent stay!",
  "comment": "Great hotel, excellent service!"
}
```

**Response:**
```json
{
  "message": "Review created successfully",
  "review": {
    "id": 1,
    "booking_id": 1,
    "rating": 5,
    "title": "Excellent stay!",
    "comment": "Great hotel, excellent service!",
    "is_verified": true,
    "created_at": "2023-02-05T00:00:00Z"
  }
}
```

---

## Admin Endpoints

### Get Dashboard Stats

**GET** `/admin/dashboard`

Get dashboard statistics (admin only).

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Query Parameters:**
- `days` (integer) - Number of days for statistics (default: 30)

**Response:**
```json
{
  "dashboard_stats": {
    "bookings": {
      "total": 150,
      "recent": 25,
      "growth_rate": 15.5
    },
    "revenue": {
      "total": 45000.00,
      "recent": 7500.00,
      "growth_rate": 12.3
    },
    "occupancy": {
      "rate": 78.5,
      "total_rooms": 100,
      "occupied_rooms": 78
    },
    "users": {
      "total": 500,
      "recent": 15
    },
    "reviews": {
      "total": 200,
      "average_rating": 4.2
    }
  },
  "period": {
    "start_date": "2023-01-01T00:00:00Z",
    "end_date": "2023-01-31T00:00:00Z",
    "days": 30
  }
}
```

### Get All Bookings

**GET** `/admin/bookings`

Get all bookings with filtering (admin only).

**Query Parameters:**
- `status` (string) - Filter by booking status
- `hotel_id` (integer) - Filter by hotel
- `user_id` (integer) - Filter by user
- `check_in_from` (string) - Filter from check-in date
- `check_in_to` (string) - Filter to check-in date
- `limit` (integer) - Number of results (default: 50)
- `offset` (integer) - Number of results to skip (default: 0)

### Get All Users

**GET** `/admin/users`

Get all users with filtering (admin only).

**Query Parameters:**
- `role` (string) - Filter by role
- `is_active` (boolean) - Filter by active status
- `search` (string) - Search in name/email
- `limit` (integer) - Number of results (default: 50)
- `offset` (integer) - Number of results to skip (default: 0)

---

## Webhook Endpoints

### Stripe Webhook

**POST** `/payments/webhook/stripe`

Handle Stripe webhook events.

**Headers:**
```
Stripe-Signature: t=timestamp,v1=signature
Content-Type: application/json
```

**Request Body:**
```json
{
  "id": "evt_1234567890",
  "object": "event",
  "type": "payment_intent.succeeded",
  "data": {
    "object": {
      "id": "pi_1234567890",
      "amount": 30000,
      "currency": "usd",
      "status": "succeeded"
    }
  }
}
```

### PayPal Webhook

**POST** `/payments/webhook/paypal`

Handle PayPal webhook events.

**Headers:**
```
PAYPAL-TRANSMISSION-SIG: signature
Content-Type: application/json
```

---

## Health Check

### Health Check

**GET** `/health`

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## Rate Limiting

Rate limits are applied per IP address and endpoint. When exceeded, the API returns a `429 Too Many Requests` status with the following response:

```json
{
  "error": "Rate limit exceeded"
}
```

Rate limit headers are included in responses:
- `X-RateLimit-Limit` - Request limit per window
- `X-RateLimit-Remaining` - Remaining requests in current window
- `X-RateLimit-Reset` - Time when the rate limit resets

---

## Pagination

List endpoints support pagination using `limit` and `offset` parameters:

- `limit` - Maximum number of items to return (default varies by endpoint)
- `offset` - Number of items to skip (default: 0)

Pagination information is included in the response:

```json
{
  "data": [...],
  "pagination": {
    "total": 100,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

---

## Timezone Handling

The API supports timezone-aware operations. Include the user's timezone in the request header:

```
X-Timezone: America/New_York
```

If not provided, UTC is used as the default timezone.

---

## Error Handling

The API uses standard HTTP status codes and returns error details in JSON format:

```json
{
  "error": "Detailed error message",
  "code": "ERROR_CODE",
  "details": {
    "field": "Additional error details"
  }
}
```

Common error scenarios:
- Invalid authentication credentials
- Insufficient permissions
- Validation errors
- Resource not found
- Business logic violations (e.g., booking conflicts)
- Rate limit exceeded
