# 🚀 Pinecone RAG Setup (5 Minutes)

Your chatbot now uses **Pinecone** for document search - way better than running ML models on Railway!

## ✅ What You Get:

- ✅ Upload docs to Pinecone (drag/drop in their dashboard)
- ✅ AI semantic search (finds meaning, not just keywords)
- ✅ Blazing fast (milliseconds)
- ✅ Free tier: 100k vectors
- ✅ No heavy packages on Railway (deploys in 2 mins!)

---

## 📋 Setup Steps:

### 1. Create Pinecone Account (1 min)

👉 Go to https://www.pinecone.io
- Click "Sign Up" (free)
- Verify email
- Login to dashboard

### 2. Create an Index (2 mins)

In Pinecone dashboard:

1. Click **"Create Index"**
2. Fill in:
   - **Name:** `ucx-chatbot` (or whatever you want)
   - **Dimensions:** `1536`
   - **Metric:** `cosine`
   - **Cloud Provider:** `AWS`
   - **Region:** `us-east-1`
3. Click **"Create Index"**

Wait 30 seconds for it to initialize.

### 3. Get Your API Key (30 seconds)

1. Click **"API Keys"** in left sidebar
2. Copy your API key (starts with `pcsk_...` or similar)

### 4. Add to Railway (1 min)

In Railway → Your Service → **Variables**:

Add these two:

```
PINECONE_API_KEY = your_key_from_step_3
PINECONE_INDEX_NAME = ucx-chatbot
```

Railway will auto-restart (~2 mins)

### 5. Test It! (30 seconds)

Once deployed:

```bash
curl https://ucxai-production.up.railway.app/setup
```

Should show: `"current_status": "Connected"`

---

## 📚 Upload Documents to Pinecone

### Option A: Pinecone Dashboard (Easiest)

1. Go to your Pinecone index
2. Click **"Upload Data"**
3. Drag/drop PDFs, TXT files
4. Pinecone auto-embeds them
5. Done! Chat with your data

### Option B: Pinecone API

```python
from pinecone import Pinecone
from openai import OpenAI

# Initialize
pc = Pinecone(api_key="your_key")
index = pc.Index("ucx-chatbot")
openai_client = OpenAI(api_key="your_openai_key")

# Get embedding
response = openai_client.embeddings.create(
    input="Your document text here",
    model="text-embedding-3-small"
)
embedding = response.data[0].embedding

# Upload to Pinecone
index.upsert(vectors=[{
    "id": "doc1",
    "values": embedding,
    "metadata": {
        "text": "Your document text",
        "source": "guide.pdf"
    }
}])
```

### Option C: Python Script (Batch Upload)

I can create a script that uploads all your PDFs automatically!

---

## 🧪 Test Your Chatbot

Once documents are uploaded:

```bash
curl -X POST https://ucxai-production.up.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What information do you have about...?"}'
```

Response will include `sources_used` showing which docs were referenced!

---

## 💰 Pricing

**Pinecone Free Tier:**
- 100,000 vectors (that's A LOT of docs!)
- 100 queries/second
- 1 index
- Perfect for most use cases

**Paid (if you need more):**
- $0.096/hour for serverless
- Pay only for what you use

**Embeddings (OpenAI API):**
- $0.02 per 1M tokens
- ~1,000 documents = $0.01
- Basically free

---

## 🎯 Architecture

```
User asks: "What are your features?"
           ↓
Your Railway Chatbot receives request
           ↓
Convert question to embedding (OpenAI API)
           ↓
Search Pinecone for similar docs
           ↓
Get top 3 relevant chunks
           ↓
Pass to Groq AI as context
           ↓
Return answer: "Based on the product guide..."
           ↓
Sources shown: ["product_guide.pdf", "features.txt"]
```

---

## 🔧 Advanced: Upload Script

Want a script to bulk upload PDFs? I can create:

```bash
python upload_to_pinecone.py my_docs/*.pdf
```

It will:
1. Extract text from PDFs
2. Chunk into pieces
3. Get embeddings via OpenAI
4. Upload to Pinecone
5. Show progress

Let me know if you want this!

---

## ✅ What's Next?

After Pinecone is set up:

1. **Upload your docs** (Pinecone dashboard or API)
2. **Test chat** (should cite sources!)
3. **Add chat widget to Lovable** (works same as before)
4. **Customers get smart answers** from your docs! 🎉

---

## 🐛 Troubleshooting

**"Pinecone not configured"**
- Check `PINECONE_API_KEY` is in Railway variables
- Check `PINECONE_INDEX_NAME` matches your index name
- Restart Railway service

**"No results found"**
- Make sure you uploaded documents to Pinecone
- Check index name is correct
- Try broader search terms

**"Embedding error"**
- Need OpenAI API key (or use Groq key, we auto-detect)
- Check API key has credits

---

## 🎉 You're All Set!

Your chatbot is now:
- ✅ Lightweight (deploys fast)
- ✅ Smart (Pinecone semantic search)
- ✅ Scalable (handles millions of docs)
- ✅ Cheap (mostly free!)

Go to Pinecone dashboard and start uploading docs!
