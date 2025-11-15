# Lovable Integration Setup Guide
## Quick Setup for Your Existing Lovable Project

Your chatbot backend is ready at: **https://ucxai-production.up.railway.app**

This guide will help you integrate it with your existing Lovable chat interface.

---

## Step 1: Set Up Database Tables in Supabase

1. Go to your **Supabase Dashboard**: https://app.supabase.com/project/xqkaioydgtlyfmwjvyhg
2. Click **SQL Editor** in the left sidebar
3. Click **+ New Query**
4. Copy the entire contents of `supabase_schema_users.sql` from this repository
5. Paste and click **Run**

This creates three tables:
- `users` - Stores Lovable user information
- `conversations` - Stores chat sessions
- `messages` - Stores individual chat messages

**Verification:** Go to **Table Editor** and you should see these three new tables.

---

## Step 2: Update CORS on Railway

Your backend needs to allow requests from your Lovable domain.

1. Go to **Railway Dashboard**: https://railway.app
2. Select your **ucxai-production** project
3. Click **Variables** tab
4. Find `ALLOWED_ORIGINS` or add it if missing
5. Update the value to include your Lovable domains:

```
ALLOWED_ORIGINS=http://localhost:5173,https://lovable.app,https://lovable.dev,https://*.lovable.app,https://*.lovable.dev
```

6. Click **Deploy** to restart with new environment variables

**Note:** Replace `*.lovable.app` with your actual Lovable domain once you know it (e.g., `https://your-project.lovable.app`)

---

## Step 3: Replace Your Chat Component

### Option A: Replace Entire Component (Recommended)

1. Copy `loveable/ChatWidgetSupabaseAuth.tsx` to your Lovable project
2. Place it at `src/components/ChatWidgetSupabaseAuth.tsx`
3. Update your route in `src/App.tsx`:

```tsx
import ChatWidgetSupabaseAuth from '@/components/ChatWidgetSupabaseAuth';

// In your routes:
<Route path="/chat" element={
  <ProtectedRoute>
    <ChatWidgetSupabaseAuth apiUrl="https://ucxai-production.up.railway.app" />
  </ProtectedRoute>
} />
```

### Option B: Update Your Existing AdminPanel.tsx

If you want to keep your existing UI, just update the API calls in your current `AdminPanel.tsx`:

```tsx
// At the top of AdminPanel.tsx
import { supabase } from '@/integrations/supabase/client';
import { useEffect, useState } from 'react';

const AdminPanel = () => {
  const [user, setUser] = useState<any>(null);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);

  // Get authenticated user
  useEffect(() => {
    const getUser = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setUser(session?.user || null);
    };
    getUser();
  }, []);

  // Update your sendMessage function:
  const sendMessage = async () => {
    if (!user) return;

    const response = await fetch('https://ucxai-production.up.railway.app/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: inputValue,
        conversation_id: currentConversationId,
        loveable_user_id: user.id,        // Supabase user ID
        email: user.email,                 // User email
        display_name: user.email,          // Use email as display name
        use_rag: true                      // Enable RAG search
      })
    });

    const data = await response.json();

    // Update conversation ID if new
    if (!currentConversationId) {
      setCurrentConversationId(data.conversation_id);
    }

    // Add assistant message to UI
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: data.response
    }]);
  };

  // Add function to load user conversations
  const loadConversations = async () => {
    if (!user?.id) return;

    const response = await fetch(
      `https://ucxai-production.up.railway.app/api/users/${user.id}/conversations`
    );
    const data = await response.json();

    // Update your conversations list
    setConversations(data.conversations);
  };

  // Call loadConversations when component mounts
  useEffect(() => {
    if (user) {
      loadConversations();
    }
  }, [user]);
};
```

---

## Step 4: Install Required Dependencies

Your Lovable project needs the `marked` package for markdown rendering:

1. In your Lovable project terminal (or local if working locally):

```bash
npm install marked
```

2. Or add to your `package.json`:

```json
{
  "dependencies": {
    "marked": "^11.0.0"
  }
}
```

---

## Step 5: Test the Integration

### Local Testing (localhost:5173)

1. Run your Lovable project locally:
```bash
npm run dev
```

2. Navigate to `/chat` in your browser
3. You should be logged in via Supabase Auth
4. Send a test message
5. Check Supabase **Table Editor** → `messages` table - you should see new records

### Production Testing

1. Deploy your Lovable project
2. Note your Lovable domain (e.g., `https://your-project.lovable.app`)
3. Update Railway `ALLOWED_ORIGINS` with your actual domain
4. Test the chat on your live Lovable site

---

## Step 6: Verify Everything Works

### ✅ Checklist

- [ ] Database tables created in Supabase
- [ ] Can see `users`, `conversations`, `messages` tables in Supabase
- [ ] CORS updated on Railway with your Lovable domain
- [ ] Chat component updated with new API calls
- [ ] `marked` package installed
- [ ] User can send messages
- [ ] Messages appear in Supabase `messages` table
- [ ] Conversations persist across page refreshes
- [ ] Sidebar shows conversation history
- [ ] Can delete conversations

### Test API Directly

```bash
# Get your Supabase user ID first
# Go to Supabase → Authentication → Users → Copy a user ID

# Test creating a conversation
curl -X POST https://ucxai-production.up.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test message",
    "loveable_user_id": "YOUR_SUPABASE_USER_ID_HERE",
    "email": "test@example.com",
    "use_rag": true
  }'

# Get user conversations
curl https://ucxai-production.up.railway.app/api/users/YOUR_SUPABASE_USER_ID_HERE/conversations
```

---

## Step 7: Optional Enhancements

### Add User Profiles Table

If you want to store user names (not just email), create a `profiles` table:

```sql
-- In Supabase SQL Editor
CREATE TABLE profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT,
  full_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own profile
CREATE POLICY "Users can read own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);

-- Policy: Users can update their own profile
CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id);
```

Then fetch the profile in your component:

```tsx
const { data: profile } = await supabase
  .from('profiles')
  .select('*')
  .eq('id', user.id)
  .single();

// Use profile.full_name instead of user.email
```

### Add Conversation Sharing

Allow users to share conversations:

```sql
ALTER TABLE conversations ADD COLUMN is_public BOOLEAN DEFAULT FALSE;
ALTER TABLE conversations ADD COLUMN share_token TEXT UNIQUE;
```

### Add Message Reactions

Store user reactions to AI responses:

```sql
CREATE TABLE message_reactions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  reaction TEXT CHECK (reaction IN ('like', 'dislike', 'helpful', 'not_helpful')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(message_id, user_id)
);
```

---

## Troubleshooting

### CORS Errors

**Error:** `Access to fetch at 'https://ucxai-production.up.railway.app/api/chat' from origin 'https://your-site.lovable.app' has been blocked by CORS policy`

**Solution:**
1. Go to Railway → ucxai-production → Variables
2. Add your Lovable domain to `ALLOWED_ORIGINS`
3. Redeploy

### User Not Authenticated

**Error:** Component shows "Please log in to use the chat"

**Solution:**
1. Check that user is logged in: `await supabase.auth.getSession()`
2. Verify Supabase client is configured correctly
3. Check that `/chat` route is protected with `<ProtectedRoute>`

### Messages Not Persisting

**Error:** Messages send but don't appear in Supabase

**Solution:**
1. Check that tables are created: `supabase_schema_users.sql` was run
2. Verify `SUPABASE_URL` and `SUPABASE_KEY` are set in Railway
3. Check Railway logs for errors: https://railway.app/dashboard

### Markdown Not Rendering

**Error:** AI responses show raw markdown (e.g., `**bold**` instead of **bold**)

**Solution:**
1. Install `marked`: `npm install marked`
2. Import: `import { marked } from 'marked'`
3. Use: `dangerouslySetInnerHTML={{ __html: marked.parse(content) }}`

### Conversations Not Loading

**Error:** Sidebar is empty or conversations don't load

**Solution:**
1. Check API response: Open Network tab in browser DevTools
2. Verify user ID is correct: `console.log(user.id)`
3. Check Supabase `conversations` table has records
4. Ensure `loveable_user_id` matches Supabase `user.id`

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                 Lovable Frontend                     │
│  ┌────────────────────────────────────────────┐    │
│  │  ChatWidgetSupabaseAuth.tsx                │    │
│  │  - Gets user from Supabase Auth            │    │
│  │  - Sends messages to Railway API           │    │
│  │  - Displays conversation history           │    │
│  └────────────────────────────────────────────┘    │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ HTTP POST /api/chat
                   │ { loveable_user_id, message, ... }
                   ↓
┌─────────────────────────────────────────────────────┐
│          Railway Backend (FastAPI)                   │
│  ┌────────────────────────────────────────────┐    │
│  │  main.py                                    │    │
│  │  - Receives message                         │    │
│  │  - Creates/gets user in Supabase            │    │
│  │  - Searches Pinecone for context (RAG)      │    │
│  │  - Calls Groq API (Llama 3.3)               │    │
│  │  - Stores messages in Supabase              │    │
│  └────────────────────────────────────────────┘    │
└──────┬─────────────────┬─────────────────┬──────────┘
       │                 │                 │
       ↓                 ↓                 ↓
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Supabase   │  │  Pinecone   │  │   Groq API  │
│  Database   │  │  Vector DB  │  │  (Llama 3.3)│
│             │  │             │  │             │
│  - users    │  │  - 30 PDFs  │  │  - Chat     │
│  - convos   │  │  - RAG      │  │  - Free!    │
│  - messages │  │  - Search   │  │             │
└─────────────┘  └─────────────┘  └─────────────┘
```

---

## API Endpoints Reference

### Send Message
```
POST /api/chat
Body: {
  message: string,
  conversation_id?: string,
  loveable_user_id: string,
  email?: string,
  display_name?: string,
  use_rag?: boolean
}
```

### Get User Conversations
```
GET /api/users/{loveable_user_id}/conversations
Response: {
  conversations: Conversation[],
  count: number
}
```

### Get Conversation Details
```
GET /api/conversations/{conversation_id}
Response: {
  conversation: Conversation,
  messages: Message[],
  message_count: number
}
```

### Delete Conversation
```
DELETE /api/conversations/{conversation_id}
```

### Get User Profile
```
GET /api/users/{loveable_user_id}
Response: {
  user: User,
  stats: { conversation_count, message_count }
}
```

---

## Next Steps

Once the integration is working:

1. **Customize the UI** - Match your Lovable theme colors
2. **Add features** - Message reactions, conversation sharing, etc.
3. **Monitor usage** - Track conversation counts in Supabase
4. **Upload more documents** - Use `upload_documents.py` to add more PDFs
5. **Configure alerts** - Set up Supabase webhooks for new messages

---

## Support

If you run into issues:

1. **Check Railway logs**: https://railway.app/dashboard → ucxai-production → Deployments → Logs
2. **Check Supabase logs**: https://app.supabase.com/project/xqkaioydgtlyfmwjvyhg/logs
3. **Check browser console**: F12 → Console tab
4. **Test API directly**: Use curl or Postman to test endpoints

Your chatbot is ready to go! 🚀
