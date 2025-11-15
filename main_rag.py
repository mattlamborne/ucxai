"""
UCX AI Chatbot API with RAG (Retrieval Augmented Generation)
Searches your documents to provide context-aware responses
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from typing import Optional, List
from datetime import datetime
import tempfile
import shutil

# Import RAG utilities
from rag_utils import (
    extract_text,
    store_document,
    get_context_for_query,
    search_similar_chunks
)

load_dotenv()

app = FastAPI(title="UCX AI Chatbot API with RAG")

# CORS Configuration
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI Provider Configuration
AI_PROVIDER = os.getenv("AI_PROVIDER", "groq").lower()

# Initialize AI client based on provider
if AI_PROVIDER == "deepseek":
    ai_client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )
    DEFAULT_MODEL = "deepseek-chat"
elif AI_PROVIDER == "groq":
    ai_client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    )
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
else:  # openai
    ai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    DEFAULT_MODEL = "gpt-4o-mini"

# Initialize Supabase client (optional - gracefully handle errors)
try:
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    SUPABASE_ENABLED = True
    print("✅ Supabase connected")
except Exception as e:
    print(f"⚠️  Supabase not available: {e}")
    print("⚠️  RAG and chat history will not be available")
    supabase = None
    SUPABASE_ENABLED = False

# Models
class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = "anonymous"
    model: Optional[str] = None
    use_rag: Optional[bool] = True  # Enable RAG by default

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    model_used: str
    tokens_used: Optional[int] = None
    sources_used: Optional[List[str]] = []  # Which documents were referenced

class DocumentUpload(BaseModel):
    title: str
    content: str
    source: Optional[str] = "manual"
    doc_type: Optional[str] = "txt"

class SearchQuery(BaseModel):
    query: str
    top_k: Optional[int] = 5

# System prompt
SYSTEM_PROMPT = """You are a helpful, friendly AI assistant.
When provided with context from documents, use that information to give accurate, specific answers.
Always cite which source you're using when referencing the provided context.
If the context doesn't contain relevant information, say so and provide a general response."""

@app.get("/")
async def root():
    return {
        "message": "UCX AI Chatbot API with RAG",
        "status": "running",
        "provider": AI_PROVIDER,
        "default_model": DEFAULT_MODEL,
        "rag_enabled": SUPABASE_ENABLED,
        "endpoints": {
            "chat": "/api/chat",
            "upload_file": "/api/documents/upload",
            "upload_text": "/api/documents/add",
            "search": "/api/documents/search",
            "list_documents": "/api/documents",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "rag_available": SUPABASE_ENABLED
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    """
    Main chat endpoint with RAG support
    Searches your documents and provides context-aware responses
    """
    try:
        model = chat_message.model or DEFAULT_MODEL
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        sources_used = []

        # Get RAG context if enabled and available
        if chat_message.use_rag and SUPABASE_ENABLED:
            try:
                context = get_context_for_query(supabase, chat_message.message, top_k=3)
                if context:
                    messages.append({
                        "role": "system",
                        "content": f"CONTEXT FROM KNOWLEDGE BASE:\n{context}"
                    })
                    # Extract source names
                    import re
                    sources = re.findall(r'\[Source \d+: (.+?)\]', context)
                    sources_used = sources
            except Exception as rag_error:
                print(f"RAG error (continuing without context): {rag_error}")

        # Get conversation history
        if chat_message.conversation_id and SUPABASE_ENABLED:
            try:
                history_response = supabase.table("messages").select("*").eq(
                    "conversation_id", chat_message.conversation_id
                ).order("created_at").execute()

                for msg in history_response.data:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            except Exception as e:
                print(f"History error: {e}")

        # Add current user message
        messages.append({
            "role": "user",
            "content": chat_message.message
        })

        # Call AI API
        completion = ai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            stream=False
        )

        assistant_response = completion.choices[0].message.content
        tokens_used = completion.usage.total_tokens if completion.usage else None

        # Create conversation ID
        conversation_id = chat_message.conversation_id or f"conv_{datetime.utcnow().timestamp()}"

        # Store in Supabase
        if SUPABASE_ENABLED:
            try:
                supabase.table("messages").insert({
                    "conversation_id": conversation_id,
                    "user_id": chat_message.user_id,
                    "role": "user",
                    "content": chat_message.message,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()

                supabase.table("messages").insert({
                    "conversation_id": conversation_id,
                    "user_id": chat_message.user_id,
                    "role": "assistant",
                    "content": assistant_response,
                    "model": model,
                    "tokens_used": tokens_used,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
            except Exception as db_error:
                print(f"Database error: {db_error}")

        return ChatResponse(
            response=assistant_response,
            conversation_id=conversation_id,
            model_used=model,
            tokens_used=tokens_used,
            sources_used=sources_used
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF, DOCX, TXT) and process it for RAG
    """
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="RAG not available (Supabase not configured)")

    try:
        # Save uploaded file temporarily
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name

        # Extract text
        doc_type = suffix[1:].lower()  # Remove the dot
        content = extract_text(tmp_path, doc_type)

        if not content:
            raise HTTPException(status_code=400, detail="Could not extract text from document")

        # Store document with embeddings
        document_id = store_document(
            supabase,
            title=file.filename,
            content=content,
            source=f"upload:{file.filename}",
            doc_type=doc_type,
            metadata={"file_size": os.path.getsize(tmp_path)}
        )

        # Clean up temp file
        os.unlink(tmp_path)

        return {
            "message": "Document uploaded and processed successfully",
            "document_id": document_id,
            "filename": file.filename,
            "doc_type": doc_type,
            "content_length": len(content)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

@app.post("/api/documents/add")
async def add_text_document(doc: DocumentUpload):
    """
    Add a text document directly (useful for prompts, snippets, etc.)
    """
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="RAG not available")

    try:
        document_id = store_document(
            supabase,
            title=doc.title,
            content=doc.content,
            source=doc.source,
            doc_type=doc.doc_type
        )

        return {
            "message": "Document added successfully",
            "document_id": document_id,
            "title": doc.title,
            "content_length": len(doc.content)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/documents/search")
async def search_documents(query: SearchQuery):
    """
    Search your documents using semantic search
    """
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="RAG not available")

    try:
        results = search_similar_chunks(supabase, query.query, top_k=query.top_k)

        return {
            "query": query.query,
            "results": results,
            "count": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/api/documents")
async def list_documents():
    """
    List all uploaded documents
    """
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="RAG not available")

    try:
        response = supabase.table("documents").select("id, title, doc_type, source, created_at").order("created_at", desc=True).execute()

        return {
            "documents": response.data,
            "count": len(response.data)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document and all its chunks
    """
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="RAG not available")

    try:
        supabase.table("documents").delete().eq("id", document_id).execute()

        return {"message": "Document deleted", "document_id": document_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print("🚀 Starting UCX AI Chatbot with RAG...")
    print(f"📚 RAG Enabled: {SUPABASE_ENABLED}")
    print(f"🌐 Running on port: {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
