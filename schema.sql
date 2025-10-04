-- ============================================================================
-- BD Law Assistant - Complete PostgreSQL Database Schema
-- ============================================================================
-- Database: bdlaw
-- Version: 1.0.0
-- Description: Comprehensive schema for legal document management,
--              user authentication, bookmarks, and usage analytics
-- Compatible with: dbdiagram.io
-- ============================================================================

-- ============================================================================
-- SCHEMA: auth (User Management, Authentication, Bookmarks)
-- Owner: Gateway Service (Spring Boot)
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS auth;

-- ============================================================================
-- TABLE: auth.users
-- Description: User accounts and authentication
-- ============================================================================
CREATE TABLE auth.users (
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

CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_users_username ON auth.users(username);
CREATE INDEX idx_users_is_active ON auth.users(is_active);

COMMENT ON TABLE auth.users IS 'User accounts with authentication details';

-- ============================================================================
-- TABLE: auth.roles
-- Description: User role definitions (USER, PREMIUM, ADMIN)
-- ============================================================================
CREATE TABLE auth.roles (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO auth.roles (name, description) VALUES
    ('ROLE_USER', 'Standard user with basic access'),
    ('ROLE_PREMIUM', 'Premium user with enhanced features'),
    ('ROLE_ADMIN', 'Administrator with full access')
ON CONFLICT (name) DO NOTHING;

COMMENT ON TABLE auth.roles IS 'Role-based access control definitions';

-- ============================================================================
-- TABLE: auth.user_roles
-- Description: Many-to-many junction table for user-role assignments
-- ============================================================================
CREATE TABLE auth.user_roles (
    user_id BIGINT REFERENCES auth.users(id) ON DELETE CASCADE,
    role_id BIGINT REFERENCES auth.roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

COMMENT ON TABLE auth.user_roles IS 'User role assignments (many-to-many)';

-- ============================================================================
-- TABLE: auth.refresh_tokens
-- Description: JWT refresh tokens for automatic token renewal
-- ============================================================================
CREATE TABLE auth.refresh_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES auth.users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_revoked BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_refresh_tokens_token ON auth.refresh_tokens(token);
CREATE INDEX idx_refresh_tokens_user_id ON auth.refresh_tokens(user_id);

COMMENT ON TABLE auth.refresh_tokens IS 'JWT refresh tokens for session management';

-- ============================================================================
-- TABLE: auth.user_bookmarks
-- Description: User bookmarks for legal documents, search results, citations
-- ============================================================================
CREATE TABLE auth.user_bookmarks (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,

    -- Foreign Key
    user_id BIGINT NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Bookmark Classification
    bookmark_type VARCHAR(50) NOT NULL DEFAULT 'search_result',
    -- Values: 'search_result', 'chat_citation', 'law_document', 'law_section'

    -- Core Identifiers
    item_id VARCHAR(200) NOT NULL,

    -- Content
    title VARCHAR(500) NOT NULL,
    excerpt TEXT,

    -- Metadata
    category VARCHAR(100),
    section VARCHAR(100),
    year VARCHAR(10),
    url VARCHAR(500),

    -- Organization
    metadata JSONB DEFAULT '{}',
    tags TEXT[],
    notes TEXT,
    folder_name VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_accessed_at TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_user_bookmark UNIQUE(user_id, item_id),
    CONSTRAINT check_bookmark_type CHECK (bookmark_type IN ('search_result', 'chat_citation', 'law_document', 'law_section'))
);

-- Indexes for bookmarks
CREATE INDEX idx_user_bookmarks_user_created ON auth.user_bookmarks(user_id, created_at DESC);
CREATE INDEX idx_user_bookmarks_user_type ON auth.user_bookmarks(user_id, bookmark_type);
CREATE INDEX idx_user_bookmarks_user_category ON auth.user_bookmarks(user_id, category) WHERE category IS NOT NULL;
CREATE INDEX idx_user_bookmarks_tags ON auth.user_bookmarks USING GIN(tags);
CREATE INDEX idx_user_bookmarks_metadata ON auth.user_bookmarks USING GIN(metadata);
CREATE INDEX idx_user_bookmarks_folder ON auth.user_bookmarks(user_id, folder_name) WHERE folder_name IS NOT NULL;

COMMENT ON TABLE auth.user_bookmarks IS 'User bookmarks with tags, folders, and notes';

-- ============================================================================
-- TABLE: auth.usage_tracking
-- Description: API usage analytics and activity tracking
-- ============================================================================
CREATE TABLE auth.usage_tracking (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms BIGINT,
    request_size BIGINT,
    response_size BIGINT,
    user_agent VARCHAR(500),
    ip_address VARCHAR(50),
    query TEXT,
    error_message TEXT
);

CREATE INDEX idx_usage_tracking_user_date ON auth.usage_tracking(user_id, date);
CREATE INDEX idx_usage_tracking_date ON auth.usage_tracking(date);
CREATE INDEX idx_usage_tracking_endpoint ON auth.usage_tracking(endpoint);

COMMENT ON TABLE auth.usage_tracking IS 'User API usage and activity tracking';

-- ============================================================================
-- TABLE: auth.api_keys
-- Description: API keys for programmatic access
-- ============================================================================
CREATE TABLE auth.api_keys (
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

COMMENT ON TABLE auth.api_keys IS 'API keys for programmatic access';

-- ============================================================================
-- TABLE: auth.audit_logs
-- Description: Security audit trail
-- ============================================================================
CREATE TABLE auth.audit_logs (
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

COMMENT ON TABLE auth.audit_logs IS 'Security audit trail for user actions';

-- ============================================================================
-- TABLE: auth.rate_limits
-- Description: Rate limiting tracking
-- ============================================================================
CREATE TABLE auth.rate_limits (
    id BIGSERIAL PRIMARY KEY,
    identifier VARCHAR(255) NOT NULL,
    endpoint VARCHAR(255),
    request_count INT DEFAULT 1,
    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    window_end TIMESTAMP
);

CREATE INDEX idx_rate_limits_identifier ON auth.rate_limits(identifier);
CREATE INDEX idx_rate_limits_window_end ON auth.rate_limits(window_end);

COMMENT ON TABLE auth.rate_limits IS 'Rate limiting tracking by user/IP';

-- ============================================================================
-- TABLE: auth.password_reset_tokens
-- Description: Password reset token management
-- ============================================================================
CREATE TABLE auth.password_reset_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES auth.users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_used BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_password_reset_tokens_token ON auth.password_reset_tokens(token);
CREATE INDEX idx_password_reset_tokens_user_id ON auth.password_reset_tokens(user_id);

COMMENT ON TABLE auth.password_reset_tokens IS 'Password reset tokens';

-- ============================================================================
-- TABLE: auth.email_verification_tokens
-- Description: Email verification token management
-- ============================================================================
CREATE TABLE auth.email_verification_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES auth.users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_used BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_email_verification_tokens_token ON auth.email_verification_tokens(token);
CREATE INDEX idx_email_verification_tokens_user_id ON auth.email_verification_tokens(user_id);

COMMENT ON TABLE auth.email_verification_tokens IS 'Email verification tokens';

-- ============================================================================
-- SCHEMA: public (Legal Documents, RAG System)
-- Owner: RAG Service (FastAPI)
-- ============================================================================

-- ============================================================================
-- TABLE: public.laws
-- Description: Bangladesh legal documents (300+ laws)
-- ============================================================================
CREATE TABLE laws (
    id SERIAL PRIMARY KEY,
    act_number INTEGER UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    title_bengali VARCHAR(500),
    full_text TEXT NOT NULL,
    full_text_bengali TEXT,
    year INTEGER,
    category VARCHAR(200),
    subcategory VARCHAR(200),
    language VARCHAR(10) DEFAULT 'en',
    url VARCHAR(500),
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_laws_act_number ON laws(act_number);
CREATE INDEX idx_laws_category ON laws(category);
CREATE INDEX idx_laws_year ON laws(year);
CREATE INDEX idx_laws_language ON laws(language);
CREATE INDEX idx_laws_fulltext ON laws USING GIN (to_tsvector('english', full_text));
CREATE INDEX idx_laws_fulltext_bengali ON laws USING GIN (to_tsvector('simple', full_text_bengali));

COMMENT ON TABLE laws IS 'Bangladesh legal documents (300+ laws)';

-- ============================================================================
-- TABLE: public.law_chunks
-- Description: Chunked legal text for RAG processing (29,219 chunks)
-- ============================================================================
CREATE TABLE law_chunks (
    id SERIAL PRIMARY KEY,
    law_id INTEGER NOT NULL REFERENCES laws(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_text_bengali TEXT,
    section_title VARCHAR(500),
    section_number VARCHAR(50),
    start_char INTEGER,
    end_char INTEGER,
    token_count INTEGER,
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(law_id, chunk_index)
);

CREATE INDEX idx_chunks_law_id ON law_chunks(law_id);
CREATE INDEX idx_chunks_section ON law_chunks(section_title);
CREATE INDEX idx_chunks_fulltext ON law_chunks USING GIN (to_tsvector('english', chunk_text));

COMMENT ON TABLE law_chunks IS 'Chunked legal text for RAG (29,219 chunks)';

-- ============================================================================
-- TABLE: public.embeddings
-- Description: Vector embeddings for semantic search (ChromaDB sync)
-- ============================================================================
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    chunk_id INTEGER NOT NULL REFERENCES law_chunks(id) ON DELETE CASCADE,
    model_name VARCHAR(200) NOT NULL,
    embedding_vector BYTEA NOT NULL,
    vector_dimension INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chunk_id, model_name)
);

CREATE INDEX idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX idx_embeddings_model ON embeddings(model_name);

COMMENT ON TABLE embeddings IS 'Vector embeddings for semantic search (384-dim)';

-- ============================================================================
-- TABLE: public.query_logs
-- Description: User query logs and analytics
-- ============================================================================
CREATE TABLE query_logs (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    query_language VARCHAR(10) DEFAULT 'en',
    response_text TEXT,
    relevant_chunks JSONB,
    model_used VARCHAR(200),
    response_time_ms INTEGER,
    user_feedback INTEGER CHECK (user_feedback >= 1 AND user_feedback <= 5),
    session_id VARCHAR(100),
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_query_logs_session ON query_logs(session_id);
CREATE INDEX idx_query_logs_created ON query_logs(created_at);

COMMENT ON TABLE query_logs IS 'Query logs for RAG system analytics';

-- ============================================================================
-- TRIGGERS AND FUNCTIONS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for auth.users
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for auth.user_bookmarks
CREATE TRIGGER update_user_bookmarks_updated_at
    BEFORE UPDATE ON auth.user_bookmarks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for laws
CREATE TRIGGER update_laws_updated_at
    BEFORE UPDATE ON laws
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Law summaries with aggregate counts
CREATE VIEW law_summaries AS
SELECT
    l.id,
    l.act_number,
    l.title,
    l.year,
    l.category,
    l.language,
    COUNT(DISTINCT lc.id) as chunk_count,
    COUNT(DISTINCT e.id) as embedding_count,
    l.scraped_at,
    l.updated_at
FROM laws l
LEFT JOIN law_chunks lc ON l.id = lc.law_id
LEFT JOIN embeddings e ON lc.id = e.chunk_id
GROUP BY l.id;

COMMENT ON VIEW law_summaries IS 'Summary view of laws with chunk and embedding counts';

-- ============================================================================
-- PERMISSIONS (Optional - Adjust as needed)
-- ============================================================================

-- Example: Grant permissions to application user
-- GRANT ALL PRIVILEGES ON SCHEMA auth TO bdlaw_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth TO bdlaw_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA auth TO bdlaw_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO bdlaw_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO bdlaw_user;

-- ============================================================================
-- DATABASE STATISTICS
-- ============================================================================
-- Current Data (as of 2025-10-05):
-- - 300+ Bangladesh laws indexed
-- - 29,219 document chunks
-- - 384-dimensional embeddings (paraphrase-multilingual-MiniLM-L12-v2)
-- - Full-text search support (English + Bengali)
-- - Semantic search via ChromaDB
-- ============================================================================
