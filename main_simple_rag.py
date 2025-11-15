"""
UCX AI Chatbot - Simple RAG Version
Uses OpenAI embeddings instead of local sentence-transformers (lighter, faster to deploy)
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
import PyPDF2
import docx

load_dotenv()

app = FastAPI(title="UCX AI Chatbot API with Simple RAG")

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

# Initialize AI client
if AI_PROVIDER == "groq":
    ai_client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    )
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
else:
    ai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    DEFAULT_MODEL = "gpt-4o-mini"

# Initialize Supabase
try:
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    SUPABASE_ENABLED = True
    print("✅ Supabase connected")
except Exception as e:
    print(f"⚠️  Supabase not available: {e}")
    supabase = None
    SUPABASE_ENABLED = False

# Models
class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = "anonymous"
    model: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    model_used: str
    tokens_used: Optional[int] = None
    context_used: Optional[str] = None

class DocumentUpload(BaseModel):
    title: str
    content: str
    doc_type: Optional[str] = "txt"

SYSTEM_PROMPT = """You are a helpful AI assistant.
When provided with context from documents, use that information to give accurate answers.
If you don't know something, say so."""

# Simple text extraction
def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def extract_text_from_docx(file_path: str) -> str:
    try:
        doc = docx.Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return ""

def simple_search(query: str, max_results: int = 3) -> str:
    """Simple keyword-based search in documents"""
    if not SUPABASE_ENABLED:
        return ""

    try:
        # Get all documents
        docs = supabase.table("documents").select("title, content").execute()

        # Simple keyword matching
        query_words = query.lower().split()
        results = []

        for doc in docs.data:
            content = doc['content'].lower()
            # Count keyword matches
            matches = sum(1 for word in query_words if word in content)
            if matches > 0:
                results.append({
                    'title': doc['title'],
                    'content': doc['content'][:500],  # First 500 chars
                    'score': matches
                })

        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)

        # Format context
        if results[:max_results]:
            context = "Relevant information from documents:\n\n"
            for i, result in enumerate(results[:max_results], 1):
                context += f"[{result['title']}]\n{result['content']}\n\n"
            return context

    except Exception as e:
        print(f"Search error: {e}")

    return ""

@app.get("/")
async def root():
    return {
        "message": "UCX AI Chatbot with Simple RAG",
        "status": "running",
        "provider": AI_PROVIDER,
        "default_model": DEFAULT_MODEL,
        "rag_enabled": SUPABASE_ENABLED
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "rag_available": SUPABASE_ENABLED}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    try:
        model = chat_message.model or DEFAULT_MODEL
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Simple document search
        context = ""
        if SUPABASE_ENABLED:
            context = simple_search(chat_message.message)
            if context:
                messages.append({"role": "system", "content": context})

        # Get conversation history
        if chat_message.conversation_id and SUPABASE_ENABLED:
            try:
                history = supabase.table("messages").select("*").eq(
                    "conversation_id", chat_message.conversation_id
                ).order("created_at").execute()

                for msg in history.data:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            except:
                pass

        messages.append({"role": "user", "content": chat_message.message})

        # Call AI
        completion = ai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )

        response = completion.choices[0].message.content
        tokens = completion.usage.total_tokens if completion.usage else None
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
                    "content": response,
                    "model": model,
                    "tokens_used": tokens,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
            except:
                pass

        return ChatResponse(
            response=response,
            conversation_id=conversation_id,
            model_used=model,
            tokens_used=tokens,
            context_used="Yes" if context else "No"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name

        doc_type = suffix[1:].lower()

        if doc_type == 'pdf':
            content = extract_text_from_pdf(tmp_path)
        elif doc_type in ['docx', 'doc']:
            content = extract_text_from_docx(tmp_path)
        else:
            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()

        os.unlink(tmp_path)

        if not content:
            raise HTTPException(status_code=400, detail="No text extracted")

        # Store document
        result = supabase.table("documents").insert({
            "title": file.filename,
            "content": content,
            "source": f"upload:{file.filename}",
            "doc_type": doc_type,
            "created_at": datetime.utcnow().isoformat()
        }).execute()

        return {
            "message": "Document uploaded",
            "document_id": result.data[0]['id'],
            "filename": file.filename,
            "content_length": len(content)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/add")
async def add_text(doc: DocumentUpload):
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        result = supabase.table("documents").insert({
            "title": doc.title,
            "content": doc.content,
            "source": "manual",
            "doc_type": doc.doc_type,
            "created_at": datetime.utcnow().isoformat()
        }).execute()

        return {"message": "Document added", "document_id": result.data[0]['id']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
async def list_documents():
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        docs = supabase.table("documents").select("id, title, doc_type, source, created_at").order("created_at", desc=True).execute()
        return {"documents": docs.data, "count": len(docs.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        supabase.table("documents").delete().eq("id", document_id).execute()
        return {"message": "Document deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print("🚀 Starting Simple RAG Chatbot...")
    print(f"📚 RAG Enabled: {SUPABASE_ENABLED}")
    uvicorn.run(app, host="0.0.0.0", port=port)
