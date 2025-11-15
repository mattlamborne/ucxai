-- Run this in your Supabase SQL Editor
-- This creates the messages table for chat history

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id TEXT NOT NULL,
    user_id TEXT DEFAULT 'anonymous',
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    model TEXT,
    tokens_used INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);

-- Optional: Enable Row Level Security (RLS)
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Policy: Allow anonymous users to read/write their own messages
CREATE POLICY "Allow public read access" ON messages
    FOR SELECT USING (true);

CREATE POLICY "Allow public insert access" ON messages
    FOR INSERT WITH CHECK (true);

-- Optional: Conversations summary view
CREATE OR REPLACE VIEW conversation_summaries AS
SELECT
    conversation_id,
    user_id,
    COUNT(*) as message_count,
    MIN(created_at) as started_at,
    MAX(created_at) as last_message_at
FROM messages
GROUP BY conversation_id, user_id;

-- Optional: Function to clean old conversations (older than 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_conversations()
RETURNS void AS $$
BEGIN
    DELETE FROM messages
    WHERE created_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE messages IS 'Stores all chat messages and conversation history';
