-- BD Law Assistant PostgreSQL Schema
-- Database: bdlaw

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS query_logs CASCADE;
DROP TABLE IF EXISTS embeddings CASCADE;
DROP TABLE IF EXISTS law_chunks CASCADE;
DROP TABLE IF EXISTS laws CASCADE;

-- Create laws table (main legal documents)
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

-- Create law_chunks table (chunked text for processing)
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

-- Create embeddings table (vector representations)
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    chunk_id INTEGER NOT NULL REFERENCES law_chunks(id) ON DELETE CASCADE,
    model_name VARCHAR(200) NOT NULL,
    embedding_vector BYTEA NOT NULL, -- Store as binary for efficiency
    vector_dimension INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chunk_id, model_name)
);

-- Create query_logs table (track user queries)
CREATE TABLE query_logs (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    query_language VARCHAR(10) DEFAULT 'en',
    response_text TEXT,
    relevant_chunks JSONB, -- Store array of chunk IDs and scores
    model_used VARCHAR(200),
    response_time_ms INTEGER,
    user_feedback INTEGER CHECK (user_feedback >= 1 AND user_feedback <= 5),
    session_id VARCHAR(100),
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for laws table
CREATE INDEX idx_laws_act_number ON laws(act_number);
CREATE INDEX idx_laws_category ON laws(category);
CREATE INDEX idx_laws_year ON laws(year);
CREATE INDEX idx_laws_language ON laws(language);

-- Create indexes for law_chunks table
CREATE INDEX idx_chunks_law_id ON law_chunks(law_id);
CREATE INDEX idx_chunks_section ON law_chunks(section_title);

-- Create indexes for embeddings table
CREATE INDEX idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX idx_embeddings_model ON embeddings(model_name);

-- Create indexes for query_logs table
CREATE INDEX idx_query_logs_session ON query_logs(session_id);
CREATE INDEX idx_query_logs_created ON query_logs(created_at);

-- Create indexes for full-text search
CREATE INDEX idx_laws_fulltext ON laws USING GIN (to_tsvector('english', full_text));
CREATE INDEX idx_laws_fulltext_bengali ON laws USING GIN (to_tsvector('simple', full_text_bengali));
CREATE INDEX idx_chunks_fulltext ON law_chunks USING GIN (to_tsvector('english', chunk_text));

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for laws table
CREATE TRIGGER update_laws_updated_at BEFORE UPDATE ON laws
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create view for commonly accessed law information
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

-- Insert sample metadata (optional)
INSERT INTO laws (act_number, title, full_text, year, category, language, url)
VALUES
    (0, 'Sample Law', 'This is a sample law for testing', 2024, 'Test', 'en', 'http://example.com')
ON CONFLICT (act_number) DO NOTHING;