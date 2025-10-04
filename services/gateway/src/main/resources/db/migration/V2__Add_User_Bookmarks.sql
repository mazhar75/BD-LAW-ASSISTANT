-- ============================================================================
-- Flyway Migration Script
-- Version: 2
-- Description: Add user_bookmarks table for bookmark sync feature
-- Author: BD Law Assistant Team
-- Date: 2025-10-04
-- ============================================================================

-- Create user_bookmarks table
CREATE TABLE IF NOT EXISTS auth.user_bookmarks (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,

    -- Foreign Key to User
    user_id BIGINT NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Bookmark Type Classification
    bookmark_type VARCHAR(50) NOT NULL DEFAULT 'search_result',
    -- Allowed values: 'search_result', 'chat_citation', 'law_document', 'law_section'

    -- Core Identifiers
    item_id VARCHAR(200) NOT NULL,  -- Unique identifier of the bookmarked item

    -- Content Fields
    title VARCHAR(500) NOT NULL,
    excerpt TEXT,

    -- Metadata Fields
    category VARCHAR(100),          -- Law category (Criminal, Civil, Constitutional, etc.)
    section VARCHAR(100),           -- Specific section reference
    year VARCHAR(10),               -- Year of law/amendment
    url VARCHAR(500),               -- Full URL to the document

    -- Extended Features
    metadata JSONB DEFAULT '{}',    -- Flexible JSON storage
    tags TEXT[],                    -- User-defined tags: ['important', 'research']
    notes TEXT,                     -- User personal notes
    folder_name VARCHAR(100),       -- Optional folder/collection name

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_accessed_at TIMESTAMP,     -- Track when user last viewed

    -- Constraints
    CONSTRAINT unique_user_bookmark UNIQUE(user_id, item_id),
    CONSTRAINT check_bookmark_type CHECK (bookmark_type IN ('search_result', 'chat_citation', 'law_document', 'law_section'))
);

-- ============================================================================
-- Indexes for Performance Optimization
-- ============================================================================

-- Most common query: Get all bookmarks for a user (sorted by created_at DESC)
CREATE INDEX idx_user_bookmarks_user_created
    ON auth.user_bookmarks(user_id, created_at DESC);

-- Filter by bookmark type
CREATE INDEX idx_user_bookmarks_user_type
    ON auth.user_bookmarks(user_id, bookmark_type);

-- Filter by category
CREATE INDEX idx_user_bookmarks_user_category
    ON auth.user_bookmarks(user_id, category)
    WHERE category IS NOT NULL;

-- Search within tags (GIN index for array operations)
CREATE INDEX idx_user_bookmarks_tags
    ON auth.user_bookmarks USING GIN(tags);

-- Search within metadata JSONB
CREATE INDEX idx_user_bookmarks_metadata
    ON auth.user_bookmarks USING GIN(metadata);

-- Find specific bookmark (composite index)
CREATE INDEX idx_user_bookmarks_lookup
    ON auth.user_bookmarks(user_id, item_id);

-- Recently accessed bookmarks
CREATE INDEX idx_user_bookmarks_last_accessed
    ON auth.user_bookmarks(user_id, last_accessed_at DESC NULLS LAST);

-- Folder organization
CREATE INDEX idx_user_bookmarks_folder
    ON auth.user_bookmarks(user_id, folder_name)
    WHERE folder_name IS NOT NULL;

-- ============================================================================
-- Trigger for Auto-updating updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_user_bookmarks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_bookmarks_updated_at
    BEFORE UPDATE ON auth.user_bookmarks
    FOR EACH ROW
    EXECUTE FUNCTION update_user_bookmarks_updated_at();

-- ============================================================================
-- Table Comments
-- ============================================================================

COMMENT ON TABLE auth.user_bookmarks IS
    'User bookmarks for legal documents, search results, and chat citations';

COMMENT ON COLUMN auth.user_bookmarks.bookmark_type IS
    'Type of bookmark: search_result, chat_citation, law_document, law_section';

COMMENT ON COLUMN auth.user_bookmarks.metadata IS
    'Flexible JSON field for storing additional context like relevance scores, court info, etc.';

COMMENT ON COLUMN auth.user_bookmarks.tags IS
    'User-defined tags for organizing bookmarks';

COMMENT ON COLUMN auth.user_bookmarks.last_accessed_at IS
    'Tracks when user last viewed this bookmark for analytics';
