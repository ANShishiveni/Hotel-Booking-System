# Docker Deployment Guide

This guide explains how to deploy the Hotel Booking System using Docker and Docker Compose.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose (included with Docker Desktop)

## Quick Start

### 1. Clone and Navigate to Project
```bash
git clone <your-repo-url>
cd Hotel-Booking-System
```

### 2. Configure Environment Variables

Edit the `docker-compose.yml` file and update the following environment variables:

```yaml
environment:
  - SECRET_KEY=your-super-secret-production-key-change-this
  - JWT_SECRET_KEY=your-jwt-secret-key-change-this
  - MAIL_USERNAME=your-email@gmail.com
  - MAIL_PASSWORD=your-app-password
  - STRIPE_SECRET_KEY=your-stripe-secret-key
  - STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
  - STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
```

### 3. Build and Start Services

```bash
# Build and start all services
docker-compose up --build

# Or run in background (detached mode)
docker-compose up -d --build
```

### 4. Access the Application

- **Application**: http://localhost:5000
- **Health Check**: http://localhost:5000/health
- **Database**: localhost:5432 (PostgreSQL)
- **Redis**: localhost:6379 (if using caching)

## Service Architecture

### Web Service (Flask App)
- **Port**: 5000
- **Image**: Built from local Dockerfile
- **Dependencies**: PostgreSQL, Redis
- **Volumes**: 
  - `./instance:/app/instance` (SQLite files)
  - `./uploads:/app/uploads` (file uploads)

### Database Service (PostgreSQL)
- **Port**: 5432
- **Image**: postgres:13
- **Database**: hotel_booking_prod
- **User**: hotel_user
- **Volume**: Persistent data storage

### Redis Service (Optional)
- **Port**: 6379
- **Image**: redis:6-alpine
- **Purpose**: Caching and session storage

## Environment Variables

### Required Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | `your-super-secret-key` |
| `JWT_SECRET_KEY` | JWT token secret | `your-jwt-secret` |
| `MAIL_USERNAME` | SMTP username | `your-email@gmail.com` |
| `MAIL_PASSWORD` | SMTP password/app password | `your-app-password` |

### Optional Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `production` |
| `HOST` | Bind host | `0.0.0.0` |
| `PORT` | Application port | `5000` |
| `ADMIN_EMAIL` | Admin notification email | `admin@namibiahotels.com` |

## Database Management

### Initialize Database
The database is automatically initialized when the PostgreSQL container starts. The `init.sql` script runs on first startup.

### Run Migrations
```bash
# Access the web container
docker-compose exec web bash

# Run Flask-Migrate commands (if configured)
flask db upgrade
```

### Backup Database
```bash
# Create backup
docker-compose exec db pg_dump -U hotel_user hotel_booking_prod > backup.sql

# Restore from backup
docker-compose exec -T db psql -U hotel_user hotel_booking_prod < backup.sql
```

## Monitoring and Logs

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs web
docker-compose logs db

# Follow logs in real-time
docker-compose logs -f web
```

### Health Check
```bash
# Check application health
curl http://localhost:5000/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000000",
  "database": "healthy",
  "version": "1.0.0",
  "service": "Hotel Booking System"
}
```

## Production Deployment

### Security Considerations
1. **Change default passwords** in docker-compose.yml
2. **Use environment files** for sensitive data:
   ```bash
   # Create .env file
   SECRET_KEY=your-secret-key
   JWT_SECRET_KEY=your-jwt-secret
   
   # Reference in docker-compose.yml
   env_file:
     - .env
   ```

3. **Enable SSL/TLS** with reverse proxy (nginx/traefik)
4. **Use Docker secrets** for sensitive data in production

### Scaling
```bash
# Scale web service
docker-compose up --scale web=3

# Use load balancer for multiple instances
```

### Updates
```bash
# Pull latest changes and rebuild
git pull
docker-compose down
docker-compose up --build -d
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using the port
   netstat -tulpn | grep :5000
   
   # Change port in docker-compose.yml
   ports:
     - "5001:5000"
   ```

2. **Database connection failed**
   ```bash
   # Check database logs
   docker-compose logs db
   
   # Verify database is running
   docker-compose ps
   ```

3. **Permission issues**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

### Clean Up
```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## Development vs Production

### Development
- Uses SQLite database (simpler setup)
- Debug mode enabled
- Hot reloading with volume mounts

### Production
- Uses PostgreSQL database
- Debug mode disabled
- Optimized for performance and security
