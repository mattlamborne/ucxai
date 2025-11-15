from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from typing import Optional, List
from datetime import datetime

load_dotenv()

app = FastAPI(title="UCX AI Chatbot API")

# CORS Configuration
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins + ["*"],  # Remove "*" in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI Provider Configuration
AI_PROVIDER = os.getenv("AI_PROVIDER", "deepseek").lower()  # deepseek, groq, or openai

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
    DEFAULT_MODEL = "llama-3.3-70b-versatile"  # Updated model
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
except Exception as e:
    print(f"⚠️  Supabase not available: {e}")
    print("⚠️  Chat history will not be saved (API will still work!)")
    supabase = None
    SUPABASE_ENABLED = False

# Models
class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = "anonymous"
    model: Optional[str] = None  # Will use DEFAULT_MODEL if not specified

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    model_used: str
    tokens_used: Optional[int] = None

class ConversationHistory(BaseModel):
    conversation_id: str
    messages: List[dict]

# System prompt - customize this for your use case
SYSTEM_PROMPT = """You are a helpful, friendly AI assistant.
Be concise but informative. Provide clear and accurate responses."""

@app.get("/")
async def root():
    return {
        "message": "UCX AI Chatbot API",
        "status": "running",
        "provider": AI_PROVIDER,
        "default_model": DEFAULT_MODEL,
        "endpoints": {
            "chat": "/api/chat",
            "health": "/health",
            "history": "/api/history/{conversation_id}"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    """
    Main chat endpoint - sends message to AI provider (DeepSeek/Groq/OpenAI) and stores in Supabase
    """
    try:
        # Use default model if not specified
        model = chat_message.model or DEFAULT_MODEL

        # Get conversation history if conversation_id exists
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if chat_message.conversation_id and SUPABASE_ENABLED:
            # Fetch previous messages from Supabase
            history_response = supabase.table("messages").select("*").eq(
                "conversation_id", chat_message.conversation_id
            ).order("created_at").execute()

            for msg in history_response.data:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Add current user message
        messages.append({
            "role": "user",
            "content": chat_message.message
        })

        # Call AI API (blazing fast!)
        completion = ai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            stream=False
        )

        assistant_response = completion.choices[0].message.content
        tokens_used = completion.usage.total_tokens if completion.usage else None

        # Create or use existing conversation_id
        conversation_id = chat_message.conversation_id or f"conv_{datetime.utcnow().timestamp()}"

        # Store messages in Supabase (if enabled)
        if SUPABASE_ENABLED:
            try:
                # Store user message
                supabase.table("messages").insert({
                    "conversation_id": conversation_id,
                    "user_id": chat_message.user_id,
                    "role": "user",
                    "content": chat_message.message,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()

                # Store assistant response
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
                print(f"Database error (continuing anyway): {db_error}")

        return ChatResponse(
            response=assistant_response,
            conversation_id=conversation_id,
            model_used=model,
            tokens_used=tokens_used
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/history/{conversation_id}")
async def get_conversation_history(conversation_id: str):
    """
    Retrieve conversation history from Supabase
    """
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Chat history not available (Supabase not configured)")

    try:
        response = supabase.table("messages").select("*").eq(
            "conversation_id", conversation_id
        ).order("created_at").execute()

        return {
            "conversation_id": conversation_id,
            "messages": response.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")

@app.delete("/api/history/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation and all its messages
    """
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Chat history not available (Supabase not configured)")

    try:
        supabase.table("messages").delete().eq(
            "conversation_id", conversation_id
        ).execute()

        return {"message": "Conversation deleted", "conversation_id": conversation_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
