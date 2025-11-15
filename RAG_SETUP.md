# 🧠 Train Your Chatbot on Your Data (RAG Setup)

**RAG (Retrieval Augmented Generation)** lets your chatbot search your PDFs, documents, and notes to give accurate, context-aware answers.

## 🚀 Quick Setup (10 minutes)

### Step 1: Run the RAG SQL Schema (5 mins)

1. Go to your Supabase project: https://xqkaioydgtlyfmwjvyhg.supabase.co
2. Click **SQL Editor** (left sidebar)
3. Copy everything from `supabase_rag_schema.sql`
4. Paste and click **Run**

This creates:
- `documents` table - stores your PDFs/files
- `document_chunks` table - stores searchable text chunks with embeddings
- `search_documents()` function - semantic search

### Step 2: Install RAG Dependencies

```bash
pip install -r requirements_rag.txt
```

This adds:
- `pypdf2` - PDF processing
- `python-docx` - Word document support
- `sentence-transformers` - AI embeddings for search

### Step 3: Upload Your Documents

**Option A: Upload via Script (Easiest)**

```bash
# Upload specific files
python upload_documents.py my_guide.pdf my_notes.txt

# Upload all PDFs in a folder
python upload_documents.py *.pdf

# Upload entire folder
python upload_documents.py --folder ./my_docs
```

**Option B: Upload via API**

```bash
# Upload a PDF
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@my_document.pdf"

# Add text directly
curl -X POST http://localhost:8000/api/documents/add \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Company FAQ",
    "content": "Q: What are your hours?\nA: 9-5 Monday-Friday",
    "doc_type": "txt"
  }'
```

### Step 4: Start the RAG-Enabled API

```bash
python main_rag.py
```

Visit http://localhost:8000 - you should see `"rag_enabled": true`

### Step 5: Test It!

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What information do you have about [your topic]?"}'
```

The chatbot will now search your documents and include relevant info in responses!

## 📚 How It Works

1. **Document Upload** → Your PDFs/docs are converted to text
2. **Chunking** → Text is split into 500-character chunks with overlap
3. **Embeddings** → Each chunk gets a 384-dimensional vector (semantic meaning)
4. **Storage** → Chunks + embeddings stored in Supabase pgvector
5. **Search** → When you ask a question:
   - Your question gets embedded
   - Most similar chunks are found (cosine similarity)
   - Relevant context is added to the AI prompt
6. **Response** → AI answers using your documents as context

## 🎯 What Can You Upload?

**Supported Formats:**
- ✅ PDF documents (`.pdf`)
- ✅ Word documents (`.docx`)
- ✅ Text files (`.txt`)
- ✅ Markdown files (`.md`)
- ✅ Direct text via API

**Best Practices:**
- 📄 **Documentation** - Product guides, manuals, FAQs
- 📋 **Notes** - Meeting notes, research, summaries
- 📊 **Data** - Reports, findings, specifications
- 💬 **Prompts** - Custom instructions, examples
- 📚 **Books** - Reference materials, chapters

**Tips:**
- Keep files text-heavy (not scanned images)
- Use clear, well-structured documents
- More documents = better context coverage
- Each document gets chunked into ~500 char pieces

## 🔧 API Endpoints

### Chat with RAG
```bash
POST /api/chat
{
  "message": "What are your product features?",
  "use_rag": true  # default, set to false to disable RAG
}

Response:
{
  "response": "Based on the product guide...",
  "sources_used": ["product_guide.pdf", "features.txt"],
  "conversation_id": "conv_123",
  "tokens_used": 250
}
```

### Upload File
```bash
POST /api/documents/upload
Form data: file=@document.pdf

Response:
{
  "document_id": "uuid",
  "filename": "document.pdf",
  "content_length": 15420
}
```

### Add Text Document
```bash
POST /api/documents/add
{
  "title": "Product Features",
  "content": "Our product has...",
  "doc_type": "txt"
}
```

### Search Documents
```bash
POST /api/documents/search
{
  "query": "pricing information",
  "top_k": 5
}

Response:
{
  "query": "pricing information",
  "results": [
    {
      "document_title": "pricing_guide.pdf",
      "content": "Our pricing starts at...",
      "similarity": 0.85
    }
  ]
}
```

### List Documents
```bash
GET /api/documents

Response:
{
  "documents": [
    {
      "id": "uuid",
      "title": "guide.pdf",
      "doc_type": "pdf",
      "created_at": "2025-01-15T..."
    }
  ],
  "count": 5
}
```

### Delete Document
```bash
DELETE /api/documents/{document_id}
```

## 💡 Example Use Cases

### Customer Support Bot
```bash
# Upload your FAQs, product docs, troubleshooting guides
python upload_documents.py faq.pdf troubleshooting.pdf product_guide.docx

# Chat answers will reference your docs
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "How do I reset my password?"}'
```

### Internal Knowledge Base
```bash
# Upload company policies, procedures, meeting notes
python upload_documents.py --folder ./company_docs

# Employees can ask questions
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "What is our vacation policy?"}'
```

### Product Assistant
```bash
# Upload product specs, datasheets, manuals
python upload_documents.py specs/*.pdf

# Get product-specific answers
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "What are the technical specifications?"}'
```

## 🎨 Customize System Prompt

Edit `main_rag.py` line 88 to customize how the AI uses your documents:

```python
SYSTEM_PROMPT = """You are a helpful customer support agent for ACME Corp.
When provided with context from our knowledge base, use it to give accurate answers.
Always cite the source document when referencing information.
If you don't find relevant information in the knowledge base, politely say so."""
```

## 📊 Performance

**Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2`
- ⚡ Fast: ~100ms per document chunk
- 💾 Lightweight: 80MB model size
- 🎯 Accurate: 384-dimensional embeddings
- 🆓 Free: Runs locally, no API costs

**Search Speed:**
- ⚡ <100ms for similarity search
- 📚 Handles thousands of documents
- 🔍 Top-K retrieval (default: 3 chunks)

**Costs:**
- Embeddings: FREE (runs locally)
- Storage: FREE (Supabase free tier: 500MB)
- AI responses: Same as before (Groq is free!)

## 🔍 Testing Your RAG Setup

### 1. Check if RAG is working:
```bash
curl http://localhost:8000/
# Should show "rag_enabled": true
```

### 2. Upload a test document:
```bash
echo "The company was founded in 2020." > test.txt
python upload_documents.py test.txt
```

### 3. Ask about it:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "When was the company founded?"}'
```

Should return: "The company was founded in 2020" with source reference!

### 4. Search directly:
```bash
curl -X POST http://localhost:8000/api/documents/search \
  -H "Content-Type: application/json" \
  -d '{"query": "founded", "top_k": 3}'
```

Should return matching chunks with similarity scores.

## 🐛 Troubleshooting

**"RAG not available"**
- Make sure you ran `supabase_rag_schema.sql` in Supabase
- Check SUPABASE_URL and SUPABASE_KEY in `.env`
- Restart the server: `python main_rag.py`

**"Could not extract text from PDF"**
- PDF might be scanned (images, not text)
- Try opening PDF and copy-pasting text manually
- Use OCR tools to convert scanned PDFs

**"No relevant documents found"**
- Make sure documents are uploaded: `curl http://localhost:8000/api/documents`
- Try more specific questions
- Lower the similarity threshold in `rag_utils.py` (line 157)

**Upload fails**
- Check file format is supported (PDF, DOCX, TXT, MD)
- Make sure file isn't corrupted
- Check file size (Supabase free tier: 500MB total)

## 🚀 Deploy with RAG

When deploying to Railway/Render:

1. Use `main_rag.py` instead of `main.py`
2. Update `railway.json` or `Dockerfile`:
   ```json
   "startCommand": "python main_rag.py"
   ```
3. Make sure `requirements_rag.txt` is installed
4. Your Supabase credentials are in environment variables

## 📈 Scaling

**For more documents:**
- Supabase free tier: 500MB storage
- Upgrade to Pro: $25/month for 8GB
- Alternative: Use Pinecone (vector DB) for millions of documents

**For better search:**
- Adjust `chunk_size` in `rag_utils.py` (default: 500 chars)
- Increase `top_k` to retrieve more context (default: 3)
- Use larger embedding models (e.g., `all-mpnet-base-v2`)

**For faster responses:**
- Cache embeddings in Redis
- Precompute common queries
- Use Groq for instant AI responses (already doing this!)

## 🎉 You're Ready!

Your chatbot can now:
- ✅ Search your PDFs and documents
- ✅ Provide context-aware answers
- ✅ Cite sources automatically
- ✅ Learn from your data
- ✅ Stay up-to-date as you add more docs

Upload your documents and start chatting! 🚀
