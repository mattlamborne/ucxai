# Lovable Integration Guide
## Undeniable AI Chatbot Integration with Lovable

This guide explains how to integrate the Undeniable AI chatbot into your Lovable website with full user authentication and conversation history.

---

## 🚀 Quick Start

Your chatbot API is live at: **https://ucxai-production.up.railway.app**

### Step 1: Set Up Database Tables

Run this SQL in your **Supabase SQL Editor** to create the required tables:

```sql
-- Copy the entire contents of supabase_schema_users.sql
-- This creates: users, conversations, and messages tables
```

See `supabase_schema_users.sql` for the complete schema.

### Step 2: Add the Chat Widget to Lovable

Copy the `ChatWidget.tsx` component to your Lovable project:

```tsx
// In your Lovable project
import ChatWidget from './components/ChatWidget';

function MyPage() {
  const { user } = useAuth(); // Your Lovable auth hook

  return (
    <div>
      <ChatWidget
        loveableUserId={user?.id}
        email={user?.email}
        displayName={user?.name}
        apiUrl="https://ucxai-production.up.railway.app"
      />
    </div>
  );
}
```

### Step 3: Update CORS (if needed)

If your Lovable domain is not already allowed, add it to Railway environment variables:

```
ALLOWED_ORIGINS=https://your-site.lovable.app,https://your-site.lovable.dev
```

Then redeploy the Railway app.

---

## 📋 API Endpoints

### Chat Endpoint
**POST** `/api/chat`

Send a message and get AI response with RAG context.

**Request:**
```json
{
  "message": "How do i raise prices without losing clients?",
  "conversation_id": "conv_1234567890",  // Optional, auto-generated if not provided
  "loveable_user_id": "user_123",         // Your Lovable user ID
  "email": "user@example.com",            // Optional
  "display_name": "John Doe",             // Optional
  "use_rag": true                         // Enable document search (default: true)
}
```

**Response:**
```json
{
  "response": "Listen mate, raising prices is...",
  "conversation_id": "conv_1234567890",
  "model_used": "llama-3.3-70b-versatile",
  "tokens_used": 456,
  "sources_used": []  // Internal only, not shown to user
}
```

---

### Get User Conversations
**GET** `/api/users/{loveable_user_id}/conversations`

Get all conversations for a specific user.

**Response:**
```json
{
  "loveable_user_id": "user_123",
  "conversations": [
    {
      "conversation_id": "conv_1234567890",
      "title": "How do i raise prices without losing clients?",
      "created_at": "2025-11-15T10:30:00Z",
      "updated_at": "2025-11-15T10:35:00Z"
    }
  ],
  "count": 1
}
```

---

### Get Conversation Details
**GET** `/api/conversations/{conversation_id}`

Get full conversation with all messages.

**Response:**
```json
{
  "conversation": {
    "conversation_id": "conv_1234567890",
    "title": "How do i raise prices without losing clients?",
    "created_at": "2025-11-15T10:30:00Z",
    "updated_at": "2025-11-15T10:35:00Z"
  },
  "messages": [
    {
      "role": "user",
      "content": "How do i raise prices without losing clients?",
      "created_at": "2025-11-15T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "Listen mate, raising prices is...",
      "created_at": "2025-11-15T10:30:05Z",
      "model": "llama-3.3-70b-versatile",
      "tokens_used": 456
    }
  ],
  "message_count": 2
}
```

---

### Delete Conversation
**DELETE** `/api/conversations/{conversation_id}`

Delete a conversation and all its messages.

**Response:**
```json
{
  "message": "Conversation deleted successfully",
  "conversation_id": "conv_1234567890"
}
```

---

### Get User Profile
**GET** `/api/users/{loveable_user_id}`

Get user profile and statistics.

**Response:**
```json
{
  "user": {
    "loveable_user_id": "user_123",
    "email": "user@example.com",
    "display_name": "John Doe",
    "created_at": "2025-11-15T10:00:00Z",
    "last_active": "2025-11-15T10:35:00Z"
  },
  "stats": {
    "conversation_count": 5,
    "message_count": 42
  }
}
```

---

## 🔐 Authentication Flow

### How User Authentication Works

1. **User logs in to Lovable** - Your Lovable auth system handles this
2. **Pass user info to ChatWidget** - Send `loveableUserId`, `email`, `displayName` as props
3. **First message creates/updates user** - Backend automatically creates user record in Supabase
4. **Conversations linked to user** - All conversations stored with `loveable_user_id`
5. **User can access history** - Widget loads user's previous conversations from server

### Example Auth Integration

```tsx
import { useAuth } from '@/hooks/useAuth'; // Your Lovable auth hook
import ChatWidget from '@/components/ChatWidget';

export default function ChatPage() {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <div>Please log in to use the chat</div>;
  }

  return (
    <ChatWidget
      loveableUserId={user.id}
      email={user.email}
      displayName={user.displayName || user.email}
      apiUrl="https://ucxai-production.up.railway.app"
    />
  );
}
```

---

## 💾 Database Schema

### users table
Stores Lovable user information.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key (auto-generated) |
| loveable_user_id | TEXT | Your Lovable user ID (unique) |
| email | TEXT | User email |
| display_name | TEXT | User display name |
| created_at | TIMESTAMP | Account creation time |
| last_active | TIMESTAMP | Last activity time |

### conversations table
Stores chat sessions.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key (auto-generated) |
| conversation_id | TEXT | Client-generated conversation ID |
| user_id | UUID | Foreign key to users.id |
| loveable_user_id | TEXT | Denormalized for quick lookups |
| title | TEXT | Conversation title (first message) |
| created_at | TIMESTAMP | Conversation start time |
| updated_at | TIMESTAMP | Last message time |

### messages table
Stores individual chat messages.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key (auto-generated) |
| conversation_id | TEXT | Conversation identifier |
| conversation_uuid | UUID | Foreign key to conversations.id |
| user_id | UUID | Foreign key to users.id |
| loveable_user_id | TEXT | Denormalized for quick lookups |
| role | TEXT | 'user' or 'assistant' |
| content | TEXT | Message content |
| model | TEXT | AI model used |
| tokens_used | INTEGER | Token count |
| sources_used | TEXT[] | RAG sources (internal only) |
| created_at | TIMESTAMP | Message timestamp |

---

## 🎨 Customization

### Styling the Widget

The `ChatWidget.tsx` component uses inline styles for easy customization. To match your Lovable theme:

```tsx
// Modify the styles object in ChatWidget.tsx
const styles = {
  container: {
    backgroundColor: '#your-bg-color',
    // ... your custom styles
  },
  // ... more style overrides
};
```

Or use the `className` prop:

```tsx
<ChatWidget
  loveableUserId={user.id}
  className="my-custom-chat-widget"
  // ... other props
/>
```

Then add CSS in your Lovable project:

```css
.my-custom-chat-widget {
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  /* ... your styles */
}
```

### Custom Example Prompts

Edit the `examplePrompts` array in `ChatWidget.tsx`:

```tsx
const examplePrompts = [
  'Your custom prompt 1',
  'Your custom prompt 2',
  'Your custom prompt 3',
  'Your custom prompt 4'
];
```

---

## 🔄 Migration from localStorage

If you were using the `test_chat.html` version with localStorage, conversations are stored locally in the browser. The new integration stores everything server-side in Supabase.

**To migrate existing conversations:**

1. No automatic migration needed - users will start fresh
2. Old conversations remain in browser localStorage (test_chat.html)
3. New conversations are stored in Supabase (Lovable integration)

---

## 🧪 Testing

### Test the API directly:

```bash
# Test chat endpoint
curl -X POST https://ucxai-production.up.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is Undeniable AI?",
    "loveable_user_id": "test_user_123",
    "email": "test@example.com",
    "use_rag": true
  }'

# Get user conversations
curl https://ucxai-production.up.railway.app/api/users/test_user_123/conversations

# Get conversation details
curl https://ucxai-production.up.railway.app/api/conversations/conv_1234567890
```

### Test the widget in Lovable:

1. Add ChatWidget to a test page
2. Log in with a test user
3. Send a message
4. Check Supabase tables to verify data is stored
5. Reload page - conversations should persist
6. Delete a conversation - should remove from sidebar

---

## 🚨 Troubleshooting

### "CORS error" when calling API

**Solution:** Add your Lovable domain to `ALLOWED_ORIGINS` in Railway environment variables.

```
ALLOWED_ORIGINS=https://your-site.lovable.app
```

### "User not found" or conversations not loading

**Solution:** Ensure you're passing `loveableUserId` to the ChatWidget:

```tsx
<ChatWidget loveableUserId={user?.id} />
```

### Messages not persisting

**Solution:** Check that:
1. Supabase tables are created (run `supabase_schema_users.sql`)
2. `SUPABASE_URL` and `SUPABASE_KEY` are set in Railway
3. Row Level Security (RLS) policies allow inserts

### Markdown not rendering

**Solution:** Install `marked` package in your Lovable project:

```bash
npm install marked
```

Or use a different markdown parser of your choice.

---

## 📊 Analytics & Monitoring

### Track Usage

Query Supabase to get analytics:

```sql
-- Total users
SELECT COUNT(*) FROM users;

-- Total conversations
SELECT COUNT(*) FROM conversations;

-- Total messages
SELECT COUNT(*) FROM messages;

-- Messages per user
SELECT loveable_user_id, COUNT(*) as message_count
FROM messages
GROUP BY loveable_user_id
ORDER BY message_count DESC;

-- Active users (last 7 days)
SELECT COUNT(DISTINCT loveable_user_id)
FROM messages
WHERE created_at > NOW() - INTERVAL '7 days';
```

---

## 💰 Costs

**Groq API:** Free (14,400 requests/day)
**Pinecone:** Free tier (100K vectors)
**OpenAI Embeddings:** $0.02 per 1M tokens (~$0.01 per 100 searches)
**Supabase:** Free tier (500MB database, 2GB bandwidth)
**Railway:** Free tier or ~$5/month for usage-based pricing

**Estimated cost for 1000 messages/day:** < $1/month

---

## 🔗 Additional Resources

- **API Base URL:** https://ucxai-production.up.railway.app
- **Health Check:** https://ucxai-production.up.railway.app/health
- **Pinecone Setup:** See `UPLOAD_GUIDE.md`
- **Document Upload:** Use `upload_documents.py`

---

## 📝 Notes

- **No Source Citations:** The AI never reveals document sources (per Undeniable AI personality)
- **RAG Enabled:** Searches 30 uploaded PDFs for context
- **Fast Responses:** 0.5-2 seconds typical (Groq API)
- **Markdown Support:** Responses are formatted with markdown
- **UK Spelling:** System prompt configured for UK English
- **Grade 6-8 Reading Level:** Responses optimized for clarity

---

## 🆘 Support

If you encounter issues:

1. Check Railway logs: https://railway.app/dashboard
2. Check Supabase logs: https://app.supabase.com/project/xqkaioydgtlyfmwjvyhg/logs
3. Test API endpoints directly with curl
4. Verify environment variables are set correctly
5. Ensure database tables are created

For Lovable-specific integration questions, refer to Lovable's documentation on embedding external components.

---

**Happy chatting! 🚀**
