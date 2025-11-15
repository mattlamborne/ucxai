-- Clean Slate Migration for Lovable Integration
-- Run this in Supabase SQL Editor to start fresh
-- WARNING: This will DELETE all existing conversation data!

-- Drop existing tables (if they exist)
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    loveable_user_id TEXT UNIQUE NOT NULL,
    email TEXT,
    display_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    loveable_user_id TEXT,
    title TEXT DEFAULT 'New conversation',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id TEXT NOT NULL,
    conversation_uuid UUID REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    loveable_user_id TEXT,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    model TEXT,
    tokens_used INTEGER,
    sources_used TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_users_loveable_id ON users(loveable_user_id);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_loveable_user_id ON conversations(loveable_user_id);
CREATE INDEX idx_conversations_updated_at ON conversations(updated_at DESC);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_conversation_uuid ON messages(conversation_uuid);
CREATE INDEX idx_messages_user_id ON messages(user_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- RLS Policies (permissive for now - tighten based on your needs)
CREATE POLICY users_select_own ON users FOR SELECT USING (true);

CREATE POLICY conversations_select_own ON conversations FOR SELECT USING (true);
CREATE POLICY conversations_insert_own ON conversations FOR INSERT WITH CHECK (true);
CREATE POLICY conversations_update_own ON conversations FOR UPDATE USING (true);
CREATE POLICY conversations_delete_own ON conversations FOR DELETE USING (true);

CREATE POLICY messages_select_own ON messages FOR SELECT USING (true);
CREATE POLICY messages_insert_own ON messages FOR INSERT WITH CHECK (true);

-- Trigger function to update conversation timestamp
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET updated_at = NOW()
    WHERE conversation_id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update conversation timestamp when new message added
CREATE TRIGGER update_conversation_timestamp_trigger
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_timestamp();

-- Verify tables created successfully
SELECT
    tablename,
    schemaname
FROM pg_tables
WHERE schemaname = 'public'
    AND tablename IN ('users', 'conversations', 'messages')
ORDER BY tablename;

-- Show table structures
\d users
\d conversations
\d messages
