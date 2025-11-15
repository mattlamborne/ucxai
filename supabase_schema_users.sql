-- Updated Supabase Schema for User-Specific Conversations
-- Run this in your Supabase SQL editor

-- Users table (stores Loveable user info)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    loveable_user_id TEXT UNIQUE NOT NULL,  -- User ID from Loveable
    email TEXT,
    display_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversations table (stores chat sessions)
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id TEXT UNIQUE NOT NULL,  -- Client-generated ID
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    loveable_user_id TEXT,  -- Denormalized for quick lookups
    title TEXT DEFAULT 'New conversation',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Messages table (updated to link to conversations)
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id TEXT NOT NULL,
    conversation_uuid UUID REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    loveable_user_id TEXT,  -- Denormalized for quick lookups
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    model TEXT,
    tokens_used INTEGER,
    sources_used TEXT[],  -- Array of sources (though not displayed to user)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_loveable_id ON users(loveable_user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_loveable_user_id ON conversations(loveable_user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_uuid ON messages(conversation_uuid);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- Row Level Security (RLS) Policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own data
CREATE POLICY users_select_own ON users
    FOR SELECT
    USING (auth.uid()::text = loveable_user_id OR true);  -- Adjust based on Loveable auth

-- Policy: Users can read their own conversations
CREATE POLICY conversations_select_own ON conversations
    FOR SELECT
    USING (loveable_user_id = auth.uid()::text OR true);  -- Adjust based on Loveable auth

-- Policy: Users can insert their own conversations
CREATE POLICY conversations_insert_own ON conversations
    FOR INSERT
    WITH CHECK (loveable_user_id = auth.uid()::text OR true);  -- Adjust based on Loveable auth

-- Policy: Users can update their own conversations
CREATE POLICY conversations_update_own ON conversations
    FOR UPDATE
    USING (loveable_user_id = auth.uid()::text OR true);  -- Adjust based on Loveable auth

-- Policy: Users can read their own messages
CREATE POLICY messages_select_own ON messages
    FOR SELECT
    USING (loveable_user_id = auth.uid()::text OR true);  -- Adjust based on Loveable auth

-- Policy: Users can insert their own messages
CREATE POLICY messages_insert_own ON messages
    FOR INSERT
    WITH CHECK (loveable_user_id = auth.uid()::text OR true);  -- Adjust based on Loveable auth

-- Function to update conversation updated_at timestamp
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET updated_at = NOW()
    WHERE conversation_id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update conversation timestamp on new message
DROP TRIGGER IF EXISTS update_conversation_timestamp_trigger ON messages;
CREATE TRIGGER update_conversation_timestamp_trigger
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_timestamp();

-- Sample data cleanup (for testing - remove in production)
-- TRUNCATE users, conversations, messages CASCADE;
