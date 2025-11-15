# Document Upload Guide

Your chatbot is **live and ready** at: https://ucxai-production.up.railway.app/

## Quick Start

### 1. Install Dependencies (if uploading locally)
```bash
pip install -r requirements.txt
```

### 2. Check Current Documents
```bash
python upload_documents.py --list
```

### 3. Upload Your Documents

**Single file:**
```bash
python upload_documents.py mydocument.pdf
```

**Multiple files:**
```bash
python upload_documents.py file1.pdf file2.txt file3.md
```

**Entire folder:**
```bash
python upload_documents.py --folder ./my_documents
```

**All PDFs in current directory:**
```bash
python upload_documents.py *.pdf
```

### 4. Test Your Chatbot

After uploading, test it:
```bash
curl -X POST https://ucxai-production.up.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What information do you have?"}'
```

## Supported File Formats

- **PDF** (.pdf) - Requires PyPDF2 (already in requirements.txt)
- **Text** (.txt)
- **Markdown** (.md)

## How It Works

1. **Reads your file** - Extracts text from PDFs or reads plain text
2. **Chunks the text** - Splits into 1000-character chunks with 200-char overlap
3. **Creates embeddings** - Uses OpenAI's text-embedding-3-small ($0.02/1M tokens)
4. **Uploads to Pinecone** - Stores vectors in your `ucx-chatbot` index
5. **Chatbot searches** - When users ask questions, finds relevant chunks

## Environment Variables Required

In your local `.env` file:
```env
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=ucx-chatbot
OPENAI_API_KEY=your_openai_api_key  # For embeddings only
```

In **Railway** (for the chatbot):
```
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=ucx-chatbot
OPENAI_API_KEY=your_openai_api_key  # For embeddings during search
```

## Costs

**OpenAI Embeddings**: $0.02 per 1 million tokens
- 1000-word document ≈ 1300 tokens
- 100 documents ≈ 130,000 tokens = **$0.003** (less than 1 cent!)

**Pinecone**: Free tier includes:
- 100K vectors (plenty for documents)
- 1 index
- $0/month

## Advanced Usage

### Delete All Documents
```bash
python upload_documents.py --delete-all
```

### View Statistics
```bash
python upload_documents.py --list
```

## Troubleshooting

### "PyPDF2 not installed"
```bash
pip install PyPDF2
```

### "OPENAI_API_KEY not set"
Add your OpenAI API key to `.env` file (needed for creating embeddings)

### Documents uploaded but chatbot doesn't use them
1. Check Railway has `OPENAI_API_KEY` set (for search embeddings)
2. Verify with: `curl https://ucxai-production.up.railway.app/` - should show `"pinecone_enabled": true`
3. Make sure you're sending `"use_rag": true` in chat requests (it's true by default)

## Next Steps

1. **Upload your documents** to Pinecone
2. **Embed the chat widget** in your Loveable site (see `frontend/ChatWidget.jsx`)
3. **Test the RAG** - ask questions about your uploaded content
4. **Monitor costs** - check OpenAI and Pinecone dashboards

Your chatbot will automatically search Pinecone for relevant context when answering questions!
