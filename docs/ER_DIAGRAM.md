# Hotel Booking System - Entity Relationship Diagram

## Database Schema ER Diagram

```mermaid
erDiagram
    USERS {
        int id PK
        string email UK
        string username UK
        string password_hash
        string first_name
        string last_name
        string phone
        boolean is_active
        boolean email_verified
        datetime last_login
        datetime created_at
        datetime updated_at
    }

    ROLES {
        int id PK
        string name UK
        text description
        json permissions
        datetime created_at
        datetime updated_at
    }

    USER_ROLES {
        int user_id FK
        int role_id FK
        datetime created_at
    }

    HOTELS {
        int id PK
        string name
        text description
        string address
        string city
        string state
        string country
        string postal_code
        string phone
        string email
        string website
        float latitude
        float longitude
        int star_rating
        json amenities
        json images
        json policies
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    ROOM_TYPES {
        int id PK
        int hotel_id FK
        string name
        text description
        decimal base_price
        int max_occupancy
        string bed_type
        int room_size
        json amenities
        json images
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    ROOMS {
        int id PK
        int hotel_id FK
        int room_type_id FK
        string room_number
        int floor
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    BOOKINGS {
        int id PK
        string booking_reference UK
        int user_id FK
        int hotel_id FK
        int room_id FK
        int room_type_id FK
        date check_in_date
        date check_out_date
        int nights
        int adults
        int children
        decimal room_rate
        decimal total_amount
        decimal tax_amount
        decimal discount_amount
        string status
        text special_requests
        text guest_notes
        datetime created_at
        datetime updated_at
        datetime confirmed_at
        datetime cancelled_at
    }

    GUESTS {
        int id PK
        int booking_id FK
        string first_name
        string last_name
        string email
        string phone
        date date_of_birth
        string nationality
        string id_number
        string passport_number
        boolean is_primary_guest
        datetime created_at
        datetime updated_at
    }

    PAYMENTS {
        int id PK
        int booking_id FK
        string payment_reference UK
        decimal amount
        string currency
        string payment_method
        string payment_provider
        string provider_transaction_id
        string status
        string payment_intent_id
        json metadata
        datetime created_at
        datetime updated_at
        datetime processed_at
    }

    REVIEWS {
        int id PK
        int hotel_id FK
        int user_id FK
        int booking_id FK
        int rating
        string title
        text comment
        boolean is_verified
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    AUDIT_LOGS {
        int id PK
        string table_name
        int record_id
        string action
        json old_values
        json new_values
        int user_id FK
        string ip_address
        text user_agent
        datetime created_at
    }

    TOKEN_BLACKLIST {
        int id PK
        string jti UK
        string token_type
        int user_id FK
        datetime revoked_at
    }

    %% Relationships
    USERS ||--o{ USER_ROLES : "has"
    ROLES ||--o{ USER_ROLES : "assigned to"
    USERS ||--o{ BOOKINGS : "makes"
    USERS ||--o{ REVIEWS : "writes"
    USERS ||--o{ AUDIT_LOGS : "performs"
    USERS ||--o{ TOKEN_BLACKLIST : "revokes"

    HOTELS ||--o{ ROOM_TYPES : "contains"
    HOTELS ||--o{ ROOMS : "has"
    HOTELS ||--o{ BOOKINGS : "receives"
    HOTELS ||--o{ REVIEWS : "receives"

    ROOM_TYPES ||--o{ ROOMS : "defines"
    ROOM_TYPES ||--o{ BOOKINGS : "booked as"

    ROOMS ||--o{ BOOKINGS : "booked"

    BOOKINGS ||--o{ GUESTS : "includes"
    BOOKINGS ||--o{ PAYMENTS : "paid by"
    BOOKINGS ||--o{ REVIEWS : "reviewed"

    %% Constraints
    BOOKINGS }|--|| USERS : "belongs to"
    BOOKINGS }|--|| HOTELS : "at"
    BOOKINGS }|--|| ROOMS : "for"
    BOOKINGS }|--|| ROOM_TYPES : "of type"
```

## Database Schema Description

### Core Entities

1. **USERS** - User accounts with authentication and profile information
2. **ROLES** - User roles for authorization (admin, manager, guest, etc.)
3. **HOTELS** - Hotel information including location, amenities, and policies
4. **ROOM_TYPES** - Room categories with pricing and specifications
5. **ROOMS** - Individual rooms within hotels
6. **BOOKINGS** - Reservation records with dates, pricing, and status
7. **GUESTS** - Guest information for each booking
8. **PAYMENTS** - Payment transactions and processing details
9. **REVIEWS** - Hotel reviews and ratings from guests
10. **AUDIT_LOGS** - Change tracking for security and compliance

### Key Features

- **Normalized Design**: Proper foreign key relationships and data integrity
- **Audit Trail**: Complete change tracking with user attribution
- **Flexible Pricing**: Support for dynamic pricing and discounts
- **Multi-currency**: Payment support for different currencies
- **Role-based Access**: Granular permissions system
- **Concurrency Control**: Optimistic locking for booking conflicts
- **Timezone Awareness**: Proper date/time handling for international bookings
- **Payment Integration**: Ready for Stripe and other payment providers
- **Review System**: Verified reviews linked to actual bookings
- **Security**: JWT token blacklisting and comprehensive logging

### Indexes and Constraints

- **Unique Constraints**: Booking references, payment references, room numbers per hotel
- **Check Constraints**: Valid dates, positive amounts, rating ranges
- **Indexes**: Optimized for common queries (dates, status, user lookups)
- **Foreign Keys**: Maintain referential integrity across all relationships
