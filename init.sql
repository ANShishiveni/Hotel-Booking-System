-- Initialize PostgreSQL database for production
-- This script runs when the PostgreSQL container starts for the first time

-- Create database if it doesn't exist (handled by POSTGRES_DB env var)
-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'Africa/Windhoek';

-- Create any additional users or permissions if needed
-- (The main user is created via environment variables)
