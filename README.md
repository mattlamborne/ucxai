# UCX AI Chatbot 🚀

**Blazing fast, open-source AI chatbot** powered by DeepSeek, replacing your slow n8n workflow.

## ⚡ Quick Start (5 minutes)

### 1. Get Your API Keys

**DeepSeek API (Cheap & Fast)** - Recommended!
1. Go to https://platform.deepseek.com
2. Sign up and create an API key
3. Copy the key
4. **Pricing**: $0.14 per 1M tokens (crazy cheap!)

**Alternative: Groq API (Free & Ultra Fast)**
1. Go to https://console.groq.com
2. Sign up and get free API key
3. 14,400 requests/day free tier

**Supabase (Free tier)**
1. Go to https://supabase.com
2. Create a new project
3. Go to Settings → API
4. Copy your `URL` and `anon/public` key

### 2. Set Up Database

1. Open your Supabase project
2. Go to **SQL Editor**
3. Copy and paste everything from `supabase_schema.sql`
4. Click **Run**

### 3. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your keys
nano .env  # or use any text editor
```

Add your keys:
```env
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your_deepseek_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
ALLOWED_ORIGINS=http://localhost:3000,https://your-lovable-site.com
```

**Want to use Groq instead?** Change `AI_PROVIDER=groq` and add `GROQ_API_KEY=...`

### 4. Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

Visit http://localhost:8000 to test!

### 5. Test the API

```bash
# Test the chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
```

## 🌐 Deploy to Production

### Option A: Railway (Recommended - Easiest)

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub"
3. Connect your repo
4. Add environment variables (GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY)
5. Deploy!

### Option B: Render

1. Go to https://render.com
2. New → Web Service
3. Connect your repo
4. Add environment variables
5. Deploy!

### Option C: Docker

```bash
# Build
docker build -t ucxai .

# Run
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your_key \
  -e SUPABASE_URL=your_url \
  -e SUPABASE_KEY=your_key \
  ucxai
```

## 🎨 Add to Your Lovable Website

### Option 1: React Component (Best)

```jsx
import ChatWidget from './frontend/ChatWidget';

function App() {
  return (
    <div>
      <ChatWidget apiUrl="https://your-api-url.com" />
    </div>
  );
}
```

### Option 2: Standalone HTML (Copy & Paste)

Open `frontend/chat-widget-standalone.html` and update line 165:

```javascript
const API_URL = 'https://your-api-url.com'; // Your deployed URL
```

Then embed in your Lovable site:

```html
<!-- Add this to your Lovable page -->
<iframe src="https://your-site.com/chat-widget-standalone.html"
        style="position:fixed; bottom:20px; right:20px;
               width:400px; height:650px; border:none; z-index:1000;">
</iframe>
```

### Option 3: Custom Integration

```javascript
// Simple fetch example
async function chat(message, conversationId = null) {
  const response = await fetch('https://your-api-url.com/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, conversation_id: conversationId })
  });

  const data = await response.json();
  return data.response;
}
```

## 🔥 Features

- ✅ **Blazing fast** - DeepSeek/Groq are 10x faster than OpenAI
- ✅ **Dirt cheap** - DeepSeek: $0.14/1M tokens (vs OpenAI $15/1M)
- ✅ **Open source friendly** - DeepSeek V3, Llama 3.1, Mixtral support
- ✅ **Chat history** - Stored in Supabase with full context
- ✅ **Multiple providers** - Switch between DeepSeek, Groq, or OpenAI
- ✅ **Embeddable** - Works on any website
- ✅ **Production ready** - Built with FastAPI

## 📊 API Endpoints

### POST /api/chat
Send a message to the AI

```json
{
  "message": "Hello!",
  "conversation_id": "optional-conversation-id",
  "user_id": "optional-user-id",
  "model": "llama-3.1-70b-versatile"
}
```

### GET /api/history/{conversation_id}
Get conversation history

### DELETE /api/history/{conversation_id}
Delete a conversation

### GET /health
Health check

## 🎯 Customize the AI

Edit `main.py` line 42 to customize the AI's personality:

```python
SYSTEM_PROMPT = """You are a helpful, friendly AI assistant.
Be concise but informative. Provide clear and accurate responses."""
```

## 🔧 Advanced Configuration

### Switch AI Providers

Update your `.env` file:

**DeepSeek (Default - Cheapest)**
```env
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-...
# Model: deepseek-chat (automatic)
```

**Groq (Free tier - Fastest)**
```env
AI_PROVIDER=groq
GROQ_API_KEY=gsk-...
# Models: llama-3.1-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768
```

**OpenAI (Most capable)**
```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
# Models: gpt-4o-mini, gpt-4o, gpt-4-turbo
```

### Change Model

Pass `model` parameter in API request:
```json
{
  "message": "Hello!",
  "model": "deepseek-chat"
}
```

### Enable CORS for Your Domain

Update `.env`:
```env
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### Add Rate Limiting

```bash
pip install slowapi
```

Add to `main.py`:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/chat")
@limiter.limit("10/minute")
async def chat(...):
    ...
```

## 🐛 Troubleshooting

**Error: DeepSeek/Groq API key not found**
- Make sure `.env` file exists and has `DEEPSEEK_API_KEY=...` (or `GROQ_API_KEY=...`)
- Check that `AI_PROVIDER=deepseek` matches your API key

**Error: Supabase connection failed**
- Check your `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Make sure you ran the SQL schema in Supabase

**Chat is slow**
- Groq should be blazing fast (1-2 seconds)
- Check your internet connection
- Try a smaller model: `llama-3.1-8b-instant`

**CORS errors in browser**
- Add your website domain to `ALLOWED_ORIGINS` in `.env`

## 📈 Monitoring & Costs

### DeepSeek Pricing (Recommended)
- **$0.14** per 1M input tokens
- **$0.28** per 1M output tokens
- ~70,000 messages for $1!
- Example: 10,000 messages/month = ~$0.14

### Groq Free Tier
- 14,400 requests/day
- ~6,000 requests/hour
- **100% FREE**

### Supabase Free Tier
- 500MB database
- 50,000 monthly active users
- 2GB bandwidth

## 🚀 Performance vs n8n

| Metric | n8n + OpenAI Assistant | UCX AI (DeepSeek) |
|--------|----------------------|-------------------|
| Response time | 3-10 seconds | 0.5-2 seconds |
| Cost per 1M tokens | $2-60 | $0.14-0.28 |
| Setup complexity | High (webhooks, etc) | Low (one API) |
| Control | Limited | Full |
| Customization | Hard | Easy |

## 📝 License

MIT - Do whatever you want with this!

## 🤝 Support

Open an issue if you need help!
