# Hotel Booking System - Entity Relationship Diagram

```mermaid
erDiagram
    USER {
        int id PK
        string email UK
        string password_hash
        string first_name
        string last_name
        string phone
        datetime created_at
        datetime updated_at
        boolean is_active
        int role_id FK
    }
    
    ROLE {
        int id PK
        string name UK
        string description
        json permissions
        datetime created_at
    }
    
    HOTEL {
        int id PK
        string name
        string address
        string city
        string state
        string country
        string postal_code
        string phone
        string email
        decimal latitude
        decimal longitude
        json amenities
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    ROOM_TYPE {
        int id PK
        int hotel_id FK
        string name
        string description
        int max_occupancy
        json amenities
        decimal base_price
        json pricing_rules
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    ROOM {
        int id PK
        int hotel_id FK
        int room_type_id FK
        string room_number UK
        string floor
        json features
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    GUEST {
        int id PK
        string first_name
        string last_name
        string email
        string phone
        string nationality
        datetime date_of_birth
        datetime created_at
        datetime updated_at
    }
    
    BOOKING {
        int id PK
        string booking_reference UK
        int hotel_id FK
        int user_id FK
        int guest_id FK
        datetime check_in
        datetime check_out
        int adults
        int children
        decimal total_amount
        string status
        string special_requests
        datetime created_at
        datetime updated_at
        string timezone
    }
    
    BOOKING_ROOM {
        int id PK
        int booking_id FK
        int room_id FK
        decimal rate
        datetime created_at
    }
    
    PAYMENT {
        int id PK
        int booking_id FK
        string payment_method
        decimal amount
        string currency
        string status
        string transaction_id
        json payment_details
        datetime created_at
        datetime updated_at
        string webhook_signature
    }
    
    REVIEW {
        int id PK
        int booking_id FK
        int user_id FK
        int rating
        string title
        string comment
        boolean is_verified
        datetime created_at
        datetime updated_at
    }
    
    AUDIT_LOG {
        int id PK
        string table_name
        int record_id
        string action
        json old_values
        json new_values
        int user_id FK
        string ip_address
        string user_agent
        datetime created_at
    }
    
    USER ||--o{ BOOKING : makes
    USER ||--o{ REVIEW : writes
    USER ||--o{ AUDIT_LOG : performs
    USER }o--|| ROLE : has
    
    HOTEL ||--o{ ROOM_TYPE : contains
    HOTEL ||--o{ ROOM : has
    HOTEL ||--o{ BOOKING : receives
    
    ROOM_TYPE ||--o{ ROOM : defines
    ROOM ||--o{ BOOKING_ROOM : included_in
    
    GUEST ||--o{ BOOKING : books_for
    
    BOOKING ||--o{ BOOKING_ROOM : contains
    BOOKING ||--o{ PAYMENT : has
    BOOKING ||--o{ REVIEW : generates
```

## Key Relationships

1. **User Management**: Users have roles with permissions, can make bookings and write reviews
2. **Hotel Structure**: Hotels contain room types and individual rooms
3. **Booking Flow**: Users book rooms through bookings, which can include multiple rooms
4. **Payment Processing**: Each booking can have multiple payments
5. **Guest Management**: Separate guest information for actual occupants
6. **Audit Trail**: Complete audit logging for all changes
7. **Reviews**: Users can review their bookings after completion
