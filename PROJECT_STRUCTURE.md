# Hotel Booking System - Project Structure

```
hotel-booking-system/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── hotel.py
│   │   ├── booking.py
│   │   ├── payment.py
│   │   └── audit.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── hotels.py
│   │   ├── bookings.py
│   │   ├── payments.py
│   │   ├── reviews.py
│   │   └── admin.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── booking_service.py
│   │   ├── payment_service.py
│   │   ├── email_service.py
│   │   └── audit_service.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── decorators.py
│   │   ├── validators.py
│   │   ├── timezone_utils.py
│   │   └── security.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   ├── booking/
│   │   │   ├── search.html
│   │   │   ├── booking_form.html
│   │   │   └── confirmation.html
│   │   └── admin/
│   │       ├── dashboard.html
│   │       └── bookings.html
│   ├── static/
│   │   ├── css/
│   │   │   ├── main.css
│   │   │   └── admin.css
│   │   ├── js/
│   │   │   ├── booking.js
│   │   │   └── payment.js
│   │   └── img/
│   ├── config.py
│   └── extensions.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_booking.py
│   ├── test_payment.py
│   ├── test_overbooking.py
│   └── test_api.py
├── migrations/
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
├── scripts/
│   ├── init_db.py
│   ├── seed_data.py
│   └── backup_db.py
├── docs/
│   ├── API_DOCS.md
│   ├── SECURITY.md
│   └── DEPLOYMENT.md
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── README.md
├── ER_DIAGRAM.md
└── PROJECT_STRUCTURE.md
```
