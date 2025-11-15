-- RAG Extension for UCX AI Chatbot
-- Run this in your Supabase SQL Editor to add document search capabilities

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents table - stores your PDFs, text files, etc.
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT, -- file path or URL
    doc_type TEXT, -- 'pdf', 'txt', 'docx', etc.
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Document chunks table - splits large documents into searchable pieces
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding vector(384), -- sentence-transformers/all-MiniLM-L6-v2 produces 384-dim vectors
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for fast similarity search
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_documents_doc_type ON documents(doc_type);

-- Function to search similar chunks
CREATE OR REPLACE FUNCTION search_documents(
    query_embedding vector(384),
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    document_title TEXT,
    content TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id AS chunk_id,
        dc.document_id,
        d.title AS document_title,
        dc.content,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE 1 - (dc.embedding <=> query_embedding) > match_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Enable RLS (Row Level Security) if needed
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- Policies: Allow public read access (adjust as needed)
CREATE POLICY "Allow public read access on documents" ON documents
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access on document_chunks" ON document_chunks
    FOR SELECT USING (true);

CREATE POLICY "Allow public insert on documents" ON documents
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public insert on document_chunks" ON document_chunks
    FOR INSERT WITH CHECK (true);

-- View: Document statistics
CREATE OR REPLACE VIEW document_stats AS
SELECT
    COUNT(DISTINCT d.id) as total_documents,
    COUNT(dc.id) as total_chunks,
    SUM(LENGTH(d.content)) as total_characters,
    COUNT(DISTINCT d.doc_type) as document_types
FROM documents d
LEFT JOIN document_chunks dc ON d.id = dc.document_id;

COMMENT ON TABLE documents IS 'Stores uploaded documents (PDFs, text files, etc.)';
COMMENT ON TABLE document_chunks IS 'Stores document chunks with embeddings for semantic search';
COMMENT ON FUNCTION search_documents IS 'Semantic search function using vector similarity';
