-- Create database if not exists (run this separately as superuser)
-- CREATE DATABASE bdlaw_users;

-- Create schema for user management
CREATE SCHEMA IF NOT EXISTS auth;

-- Users table
CREATE TABLE IF NOT EXISTS auth.users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    phone_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_email_verified BOOLEAN DEFAULT FALSE,
    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMP
);

-- Create index for faster lookups
CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_users_username ON auth.users(username);
CREATE INDEX idx_users_is_active ON auth.users(is_active);

-- Roles table
CREATE TABLE IF NOT EXISTS auth.roles (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default roles
INSERT INTO auth.roles (name, description) VALUES
    ('ROLE_USER', 'Standard user with basic access'),
    ('ROLE_PREMIUM', 'Premium user with enhanced features'),
    ('ROLE_ADMIN', 'Administrator with full access')
ON CONFLICT (name) DO NOTHING;

-- User roles junction table
CREATE TABLE IF NOT EXISTS auth.user_roles (
    user_id BIGINT REFERENCES auth.users(id) ON DELETE CASCADE,
    role_id BIGINT REFERENCES auth.roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

-- API keys table for programmatic access
CREATE TABLE IF NOT EXISTS auth.api_keys (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES auth.users(id) ON DELETE CASCADE,
    key_value VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    rate_limit_override INT,
    allowed_ips TEXT,
    permissions JSONB
);

CREATE INDEX idx_api_keys_key_value ON auth.api_keys(key_value);
CREATE INDEX idx_api_keys_user_id ON auth.api_keys(user_id);
CREATE INDEX idx_api_keys_is_active ON auth.api_keys(is_active);

-- Refresh tokens table for JWT token refresh
CREATE TABLE IF NOT EXISTS auth.refresh_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES auth.users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_revoked BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_refresh_tokens_token ON auth.refresh_tokens(token);
CREATE INDEX idx_refresh_tokens_user_id ON auth.refresh_tokens(user_id);

-- Audit log table for security
CREATE TABLE IF NOT EXISTS auth.audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES auth.users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    status VARCHAR(20),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON auth.audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON auth.audit_logs(created_at);
CREATE INDEX idx_audit_logs_action ON auth.audit_logs(action);

-- Rate limit tracking table
CREATE TABLE IF NOT EXISTS auth.rate_limits (
    id BIGSERIAL PRIMARY KEY,
    identifier VARCHAR(255) NOT NULL, -- Can be user_id, api_key, or IP
    endpoint VARCHAR(255),
    request_count INT DEFAULT 1,
    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    window_end TIMESTAMP
);

CREATE INDEX idx_rate_limits_identifier ON auth.rate_limits(identifier);
CREATE INDEX idx_rate_limits_window_end ON auth.rate_limits(window_end);

-- Password reset tokens
CREATE TABLE IF NOT EXISTS auth.password_reset_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES auth.users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_used BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_password_reset_tokens_token ON auth.password_reset_tokens(token);
CREATE INDEX idx_password_reset_tokens_user_id ON auth.password_reset_tokens(user_id);

-- Email verification tokens
CREATE TABLE IF NOT EXISTS auth.email_verification_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES auth.users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_used BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_email_verification_tokens_token ON auth.email_verification_tokens(token);
CREATE INDEX idx_email_verification_tokens_user_id ON auth.email_verification_tokens(user_id);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for users table
CREATE TRIGGER update_users_updated_at BEFORE UPDATE
    ON auth.users FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON SCHEMA auth TO bdlaw_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth TO bdlaw_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA auth TO bdlaw_user;