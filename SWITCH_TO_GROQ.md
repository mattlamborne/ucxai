# Switch to Groq (100% FREE)

If you want to test immediately without adding funds to DeepSeek, use Groq's free tier:

## Steps:

1. **Get Groq API Key** (1 minute)
   - Go to https://console.groq.com
   - Sign up (it's free!)
   - Click "API Keys" → "Create API Key"
   - Copy the key (starts with `gsk_`)

2. **Update your `.env` file**:

```env
# Change these two lines:
AI_PROVIDER=groq
# Add this line:
GROQ_API_KEY=gsk_your_groq_key_here

# Keep everything else the same:
DEEPSEEK_API_KEY=sk-d0a03da09ea74de3bff5d8e4996f9d2e
SUPABASE_URL=https://xqkaioydgtlyfmwjvyhg.supabase.co
SUPABASE_KEY=eyJhbGc...
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

3. **Done!** Run `python main.py` and you're live!

## Groq Free Tier:
- ✅ **14,400 requests per day**
- ✅ **6,000 requests per hour**
- ✅ **Ultra fast** (even faster than DeepSeek!)
- ✅ **Models**: Llama 3.1 70B, Mixtral, and more
- ✅ **100% FREE forever**

## When to Use What:

| Provider | Best For | Cost | Speed |
|----------|----------|------|-------|
| **Groq** | Testing, low-medium traffic | FREE | ⚡⚡⚡ Fastest |
| **DeepSeek** | High traffic, production | $0.14/1M | ⚡⚡ Very fast |
| **OpenAI** | Most advanced responses | $2-60/1M | ⚡ Standard |

You can switch between providers anytime by changing `AI_PROVIDER` in `.env`!
