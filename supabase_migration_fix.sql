-- Fix for existing tables migration
-- Run this if you got "column does not exist" errors

-- OPTION 1: Drop existing tables and start fresh (RECOMMENDED for dev)
-- WARNING: This will delete all existing conversation data!
-- Uncomment these lines if you want a clean slate:

-- DROP TABLE IF EXISTS messages CASCADE;
-- DROP TABLE IF EXISTS conversations CASCADE;
-- DROP TABLE IF EXISTS users CASCADE;

-- Then run the full supabase_schema_users.sql after uncommenting above


-- OPTION 2: Alter existing tables to add missing columns
-- Use this if you have data you want to keep

-- Check if tables exist and add missing columns
DO $$
BEGIN
    -- Add columns to users table if missing
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'users') THEN
        -- Add loveable_user_id if missing
        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name='users' AND column_name='loveable_user_id') THEN
            ALTER TABLE users ADD COLUMN loveable_user_id TEXT UNIQUE;
        END IF;

        -- Add display_name if missing
        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name='users' AND column_name='display_name') THEN
            ALTER TABLE users ADD COLUMN display_name TEXT;
        END IF;

        -- Add last_active if missing
        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name='users' AND column_name='last_active') THEN
            ALTER TABLE users ADD COLUMN last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        END IF;
    END IF;

    -- Add columns to conversations table if missing
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'conversations') THEN
        -- Add conversation_id if missing
        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name='conversations' AND column_name='conversation_id') THEN
            ALTER TABLE conversations ADD COLUMN conversation_id TEXT UNIQUE;
        END IF;

        -- Add user_id if missing
        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name='conversations' AND column_name='user_id') THEN
            ALTER TABLE conversations ADD COLUMN user_id UUID;
        END IF;

        -- Add loveable_user_id if missing
        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name='conversations' AND column_name='loveable_user_id') THEN
            ALTER TABLE conversations ADD COLUMN loveable_user_id TEXT;
        END IF;

        -- Add title if missing
        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name='conversations' AND column_name='title') THEN
            ALTER TABLE conversations ADD COLUMN title TEXT DEFAULT 'New conversation';
        END IF;

        -- Add updated_at if missing
        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name='conversations' AND column_name='updated_at') THEN
            ALTER TABLE conversations ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        END IF;
    END IF;

    -- Add columns to messages table if missing
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'messages') THEN
        -- Add conversation_uuid if missing (THIS IS THE ONE CAUSING THE ERROR!)
        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name='messages' AND column_name='conversation_uuid') THEN
            ALTER TABLE messages ADD COLUMN conversation_uuid UUID;
        END IF;

        -- Add user_id if missing
        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name='messages' AND column_name='user_id') THEN
            ALTER TABLE messages ADD COLUMN user_id UUID;
        END IF;

        -- Add loveable_user_id if missing
        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name='messages' AND column_name='loveable_user_id') THEN
            ALTER TABLE messages ADD COLUMN loveable_user_id TEXT;
        END IF;

        -- Add sources_used if missing
        IF NOT EXISTS (SELECT FROM information_schema.columns
                      WHERE table_name='messages' AND column_name='sources_used') THEN
            ALTER TABLE messages ADD COLUMN sources_used TEXT[];
        END IF;
    END IF;
END $$;

-- Now create any missing tables (if they don't exist at all)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    loveable_user_id TEXT UNIQUE NOT NULL,
    email TEXT,
    display_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    loveable_user_id TEXT,
    title TEXT DEFAULT 'New conversation',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
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

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_loveable_id ON users(loveable_user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_loveable_user_id ON conversations(loveable_user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_uuid ON messages(conversation_uuid);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- Add foreign key constraints if they don't exist
DO $$
BEGIN
    -- Add user_id foreign key to conversations
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'conversations_user_id_fkey'
    ) THEN
        ALTER TABLE conversations
        ADD CONSTRAINT conversations_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;

    -- Add conversation_uuid foreign key to messages
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'messages_conversation_uuid_fkey'
    ) THEN
        ALTER TABLE messages
        ADD CONSTRAINT messages_conversation_uuid_fkey
        FOREIGN KEY (conversation_uuid) REFERENCES conversations(id) ON DELETE CASCADE;
    END IF;

    -- Add user_id foreign key to messages
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'messages_user_id_fkey'
    ) THEN
        ALTER TABLE messages
        ADD CONSTRAINT messages_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS users_select_own ON users;
DROP POLICY IF EXISTS conversations_select_own ON conversations;
DROP POLICY IF EXISTS conversations_insert_own ON conversations;
DROP POLICY IF EXISTS conversations_update_own ON conversations;
DROP POLICY IF EXISTS messages_select_own ON messages;
DROP POLICY IF EXISTS messages_insert_own ON messages;

-- Create RLS policies (allowing all for now - adjust based on your auth setup)
CREATE POLICY users_select_own ON users FOR SELECT USING (true);
CREATE POLICY conversations_select_own ON conversations FOR SELECT USING (true);
CREATE POLICY conversations_insert_own ON conversations FOR INSERT WITH CHECK (true);
CREATE POLICY conversations_update_own ON conversations FOR UPDATE USING (true);
CREATE POLICY messages_select_own ON messages FOR SELECT USING (true);
CREATE POLICY messages_insert_own ON messages FOR INSERT WITH CHECK (true);

-- Create or replace trigger function
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET updated_at = NOW()
    WHERE conversation_id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if exists
DROP TRIGGER IF EXISTS update_conversation_timestamp_trigger ON messages;

-- Create trigger
CREATE TRIGGER update_conversation_timestamp_trigger
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_timestamp();

-- Verify tables exist
SELECT
    tablename,
    schemaname
FROM pg_tables
WHERE schemaname = 'public'
    AND tablename IN ('users', 'conversations', 'messages')
ORDER BY tablename;
