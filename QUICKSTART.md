# 🚀 Quick Start Guide

Your chatbot is **ready to go!** Just need to add Supabase credentials.

## ✅ What's Already Done

- ✅ DeepSeek API key configured
- ✅ FastAPI backend created
- ✅ Chat widgets built
- ✅ Deployment configs ready

## 📋 Next Steps (10 minutes)

### Step 1: Set Up Supabase (5 mins)

1. Go to https://supabase.com and create a free account
2. Click "New Project"
3. Name it whatever you want (e.g., "ucx-chatbot")
4. Wait for it to provision (~2 mins)
5. Go to **Settings** → **API**
6. Copy these two values:
   - **Project URL** (looks like `https://xxxxx.supabase.co`)
   - **anon public key** (starts with `eyJ...`)

### Step 2: Create the Database Table (2 mins)

1. In your Supabase project, click **SQL Editor** (left sidebar)
2. Click "New Query"
3. Copy the entire contents of `supabase_schema.sql` from this repo
4. Paste it into the SQL editor
5. Click **Run** (or press Ctrl+Enter)
6. You should see "Success. No rows returned"

### Step 3: Update Your .env File (1 min)

Open `.env` file and update these lines:

```env
SUPABASE_URL=https://your-actual-project-url.supabase.co
SUPABASE_KEY=your-actual-anon-key-here
```

Your `.env` should now look like:
```env
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-d0a03da09ea74de3bff5d8e4996f9d2e
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Step 4: Test Locally (2 mins)

```bash
# Install dependencies (if not already done)
pip install -r requirements.txt

# Start the server
python main.py
```

You should see:
```
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 5: Test It! (1 min)

Open another terminal and test:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello! Can you introduce yourself?"}'
```

You should get a response from DeepSeek! 🎉

### Step 6: Test the Chat Widget

Open `frontend/chat-widget-standalone.html` in your browser:

```bash
# macOS
open frontend/chat-widget-standalone.html

# Linux
xdg-open frontend/chat-widget-standalone.html

# Windows
start frontend/chat-widget-standalone.html
```

Click the chat button and start chatting!

## 🚀 Deploy to Production

### Option 1: Railway (Easiest)

1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select this repository
5. Add environment variables:
   - `DEEPSEEK_API_KEY` = `sk-d0a03da09ea74de3bff5d8e4996f9d2e`
   - `SUPABASE_URL` = your Supabase URL
   - `SUPABASE_KEY` = your Supabase key
   - `ALLOWED_ORIGINS` = your Lovable site URL
6. Deploy!
7. Railway will give you a public URL (e.g., `https://your-app.railway.app`)

### Option 2: Render

1. Go to https://render.com
2. New → Web Service
3. Connect your GitHub repo
4. Choose "Docker" as environment
5. Add the same environment variables as above
6. Deploy!

## 🎨 Add to Your Lovable Website

Once deployed, update your Lovable site with:

```html
<!-- Add this to your Lovable page -->
<div id="chat-root"></div>
<script>
  const API_URL = 'https://your-app.railway.app'; // Your deployed URL

  // Simple chat integration
  fetch(API_URL + '/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: 'Hello!' })
  })
  .then(r => r.json())
  .then(data => console.log(data.response));
</script>
```

Or use the full React widget from `frontend/ChatWidget.jsx`

## 💡 Tips

- **Chat History**: Already enabled! Each conversation gets a unique ID
- **Customize AI**: Edit `SYSTEM_PROMPT` in `main.py` (line 52)
- **Switch to Groq**: Change `AI_PROVIDER=groq` in `.env` for 100% free tier
- **Monitor Usage**: Check DeepSeek dashboard for token usage

## 🐛 Troubleshooting

**Server won't start?**
- Check that all values in `.env` are filled in
- Make sure Python 3.11+ is installed

**No response from AI?**
- Test your DeepSeek API key at https://platform.deepseek.com
- Check Supabase connection in the dashboard

**Chat widget not loading?**
- Update `API_URL` in the widget HTML/JS
- Check CORS settings in `.env`

## 📊 What You're Getting

- **Speed**: 0.5-2 second responses (vs 3-10 with n8n)
- **Cost**: $0.14 per 1M tokens (~70,000 messages for $1)
- **Free tier**: Groq is 100% free (14,400 requests/day)

You're all set! 🎉
