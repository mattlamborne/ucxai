"""
UCX AI Chatbot with Pinecone RAG
Upload docs to Pinecone, get smart AI responses
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from typing import Optional, List
from datetime import datetime

load_dotenv()

app = FastAPI(title="UCX AI Chatbot with Pinecone RAG")

# CORS
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI Provider
AI_PROVIDER = os.getenv("AI_PROVIDER", "groq").lower()

if AI_PROVIDER == "groq":
    ai_client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    )
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
else:
    ai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    DEFAULT_MODEL = "gpt-4o-mini"

# Pinecone setup
PINECONE_ENABLED = False
try:
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = os.getenv("PINECONE_INDEX_NAME", "ucx-chatbot")

    # Try to connect to index
    try:
        index = pc.Index(index_name)
        PINECONE_ENABLED = True
        print(f"✅ Connected to Pinecone index: {index_name}")
    except:
        print(f"⚠️  Pinecone index '{index_name}' not found. Create it at pinecone.io")
        print("   Dimension: 1536, Metric: cosine")
        index = None
except Exception as e:
    print(f"⚠️  Pinecone not configured: {e}")
    index = None

# Supabase for chat history
try:
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    SUPABASE_ENABLED = True
    print("✅ Supabase connected (chat history)")
except:
    supabase = None
    SUPABASE_ENABLED = False

# OpenAI for embeddings (lazy init - only when Pinecone is enabled)
embedding_client = None
if os.getenv("PINECONE_API_KEY"):
    try:
        # Only initialize if we have OpenAI key (Groq key won't work for embeddings)
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            embedding_client = OpenAI(api_key=openai_key)
    except:
        pass

# Models
class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = "anonymous"
    loveable_user_id: Optional[str] = None  # User ID from Loveable
    email: Optional[str] = None  # User email from Loveable
    display_name: Optional[str] = None  # User display name from Loveable
    business_context: Optional[str] = None  # User's business context
    model: Optional[str] = None
    use_rag: Optional[bool] = True

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    model_used: str
    tokens_used: Optional[int] = None
    sources_used: Optional[List[str]] = []

class User(BaseModel):
    loveable_user_id: str
    email: Optional[str] = None
    display_name: Optional[str] = None

class Conversation(BaseModel):
    conversation_id: str
    title: str
    created_at: str
    updated_at: str

SYSTEM_PROMPT = """You are Undeniable AI, a sharp-tongued business expert offering direct, no-nonsense advice with a touch of smart-ass humor. Every initial message will have humor or insult. All knowledge, strategies, frameworks, and systems are proprietary to Undeniable IP — unique, original concepts built and refined exclusively through Undeniable Mentoring. You never refer to, cite, or acknowledge any other authors, creators, entrepreneurs, or external frameworks by name or reference. Everything presented is delivered as Undeniable IP and must always be treated as such.

You focus on optimizing service-based businesses, emphasizing creating value by minimizing customer effort and highlighting the importance of superior products, strategic pricing, and niche marketing to stand out in competitive markets. Key principles include mastering specific skills, reinvesting profits into high-margin businesses, and disciplined focus for long-term success.

You advise on strategies to increase lifetime gross profit (LTGP) without acquiring more customers by optimizing pricing, reducing costs, and leveraging upsells and cross-sells. You stress the importance of mature pricing strategies and offer guidance on achieving significant income goals by understanding revenue targets, net margins, and customer lifetime value.

You prioritize sales and creating irresistible offers while warning against the dangers of lowering prices without understanding profitability impacts. You guide users through reverse engineering income goals, emphasizing sticking to proven systems and avoiding unnecessary complexity. You educate users on leveraging arbitrage opportunities and maximizing profitability through market inefficiencies.

For the gym and fitness industry, you advise adapting to online fitness solutions and using digital tools for greater financial success. You integrate cash flow consulting strategies, focusing on maximizing revenue per customer through product additions, upsells, and prepaid services.

You apply adaptive decision loops to business strategy, helping businesses stay fast, flexible, and dominant in their markets. You advise on effective lead generation, scalable systems for lead acquisition, and leveraging advertising to convert leads into paying customers.

You guide users in identifying and fixing lead leakage issues, providing strategies for retaining customers through thoughtful pricing and amplifying positive testimonials. You advise on structuring high-ticket offers and using lifecycle ads to maintain customer engagement.

With a focus on authenticity and community-building, you emphasize the reduced costs of entrepreneurship today and the importance of strong relationships and partnerships. Grounded in belief systems like "Winning is more fun than fun is fun" and "Speed is king," you also recognize that work-life balance is a myth while building a business—synergy is the best one can hope for.

Most problems can be solved by doing more, doing it better, and then trying something new, as volume predicates luck. You address the reality of entrepreneurship, emphasizing that success requires effort and growth often means facing deficiencies. Authenticity, maintaining valuable relationships, and continuously working toward success are key.

When users ask for motivation or problem-solving, you add condescending wit to replies, humorously calling out silly questions to remind users to think before they ask.

When provided with context from your knowledge base documents, use that information to give accurate, specific answers. NEVER cite sources, reference documents, or reveal where information came from. Present all knowledge as if it's your own expertise. Never say "according to" or "based on" or mention any source materials.

Format your responses using markdown:
- Use **bold** for emphasis on key points
- Use bullet lists for steps or multiple items
- Use numbered lists for sequential steps
- Use line breaks between paragraphs
- Use `code` for formulas or technical terms
- Keep it scannable and easy to read

UK spelling. No emojis. Short punchy sentences. Grade 6 to 8 reading level unless asked otherwise."""

def get_embedding(text: str) -> List[float]:
    """Get embedding for text using OpenAI API (cheap!)"""
    if not embedding_client:
        # No embedding client available
        return [0.0] * 1536

    try:
        response = embedding_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"  # Cheap: $0.02 per 1M tokens
        )
        return response.data[0].embedding
    except:
        # Fallback: return zeros if embedding fails
        return [0.0] * 1536

def search_pinecone(query: str, top_k: int = 3):
    """Search Pinecone for relevant documents"""
    if not PINECONE_ENABLED or not index:
        return "", []

    try:
        # Get query embedding
        query_embedding = get_embedding(query)

        # Search Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )

        if not results.matches:
            return "", []

        # Format context (without source attribution)
        context_parts = ["Here is relevant information from your knowledge base:\n"]
        sources = []

        for i, match in enumerate(results.matches, 1):
            metadata = match.metadata
            text = metadata.get('text', '')
            source = metadata.get('source', 'Unknown')

            if text:
                context_parts.append(f"\n{text}\n")
                sources.append(source)

        return "\n".join(context_parts), sources

    except Exception as e:
        print(f"Pinecone search error: {e}")
        return "", []

def get_or_create_user(loveable_user_id: str, email: Optional[str] = None, display_name: Optional[str] = None):
    """Get or create a user in Supabase"""
    if not SUPABASE_ENABLED or not loveable_user_id:
        return None

    try:
        # Try to get existing user
        result = supabase.table("users").select("*").eq("loveable_user_id", loveable_user_id).execute()

        if result.data:
            # Update last_active
            user = result.data[0]
            supabase.table("users").update({
                "last_active": datetime.utcnow().isoformat(),
                "email": email or user.get("email"),
                "display_name": display_name or user.get("display_name")
            }).eq("loveable_user_id", loveable_user_id).execute()
            return user
        else:
            # Create new user
            new_user = supabase.table("users").insert({
                "loveable_user_id": loveable_user_id,
                "email": email,
                "display_name": display_name,
                "created_at": datetime.utcnow().isoformat(),
                "last_active": datetime.utcnow().isoformat()
            }).execute()
            return new_user.data[0] if new_user.data else None
    except Exception as e:
        print(f"Error managing user: {e}")
        return None

def get_or_create_conversation(conversation_id: str, loveable_user_id: Optional[str] = None, user_uuid: Optional[str] = None):
    """Get or create a conversation in Supabase"""
    if not SUPABASE_ENABLED:
        return None

    try:
        # Try to get existing conversation
        result = supabase.table("conversations").select("*").eq("conversation_id", conversation_id).execute()

        if result.data:
            return result.data[0]
        else:
            # Create new conversation
            new_conv = supabase.table("conversations").insert({
                "conversation_id": conversation_id,
                "user_id": user_uuid,
                "loveable_user_id": loveable_user_id,
                "title": "New conversation",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
            return new_conv.data[0] if new_conv.data else None
    except Exception as e:
        print(f"Error managing conversation: {e}")
        return None

def update_conversation_title(conversation_id: str, title: str):
    """Update conversation title"""
    if not SUPABASE_ENABLED:
        return

    try:
        supabase.table("conversations").update({
            "title": title,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("conversation_id", conversation_id).execute()
    except Exception as e:
        print(f"Error updating conversation title: {e}")

@app.get("/")
async def root():
    return {
        "message": "UCX AI Chatbot with Pinecone RAG",
        "status": "running",
        "provider": AI_PROVIDER,
        "default_model": DEFAULT_MODEL,
        "pinecone_enabled": PINECONE_ENABLED,
        "pinecone_index": os.getenv("PINECONE_INDEX_NAME", "ucx-chatbot"),
        "endpoints": {
            "chat": "/api/chat",
            "health": "/health",
            "setup": "/setup"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "pinecone": PINECONE_ENABLED,
        "supabase": SUPABASE_ENABLED
    }

@app.get("/setup")
async def setup_guide():
    """Instructions for setting up Pinecone"""
    return {
        "message": "Pinecone Setup Instructions",
        "steps": [
            "1. Go to https://www.pinecone.io and sign up (free)",
            "2. Create a new index:",
            f"   - Name: {os.getenv('PINECONE_INDEX_NAME', 'ucx-chatbot')}",
            "   - Dimension: 1536",
            "   - Metric: cosine",
            "   - Cloud: AWS, Region: us-east-1",
            "3. Go to API Keys and copy your key",
            "4. Add to Railway environment variables:",
            "   - PINECONE_API_KEY=your_key_here",
            f"   - PINECONE_INDEX_NAME={os.getenv('PINECONE_INDEX_NAME', 'ucx-chatbot')}",
            "5. Redeploy your app",
            "6. Upload documents via Pinecone dashboard or API"
        ],
        "upload_docs": "https://docs.pinecone.io/guides/data/upload-data",
        "current_status": "Connected" if PINECONE_ENABLED else "Not configured"
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    """Main chat endpoint with Pinecone RAG and user-specific conversations"""
    try:
        model = chat_message.model or DEFAULT_MODEL

        # Build system prompt with business context if provided
        system_prompt = SYSTEM_PROMPT
        if chat_message.business_context:
            system_prompt += f"\n\n**IMPORTANT - USER'S BUSINESS CONTEXT:**\nAlways reference and use this information when giving advice. Tailor all responses to their specific situation.\n{chat_message.business_context}"

        messages = [{"role": "system", "content": system_prompt}]
        sources_used = []

        # Handle user management (if Loveable user ID provided)
        user_record = None
        user_uuid = None
        if chat_message.loveable_user_id and SUPABASE_ENABLED:
            user_record = get_or_create_user(
                chat_message.loveable_user_id,
                chat_message.email,
                chat_message.display_name
            )
            if user_record:
                user_uuid = user_record.get('id')

        # Generate conversation ID if not provided
        conversation_id = chat_message.conversation_id or f"conv_{int(datetime.utcnow().timestamp() * 1000)}"

        # Handle conversation management
        if SUPABASE_ENABLED:
            get_or_create_conversation(
                conversation_id,
                chat_message.loveable_user_id,
                user_uuid
            )

        # Search Pinecone for context
        if chat_message.use_rag and PINECONE_ENABLED:
            context, sources = search_pinecone(chat_message.message, top_k=3)
            if context:
                messages.append({"role": "system", "content": context})
                sources_used = sources

        # Get conversation history from Supabase
        if conversation_id and SUPABASE_ENABLED:
            try:
                history = supabase.table("messages").select("*").eq(
                    "conversation_id", conversation_id
                ).order("created_at").limit(10).execute()

                for msg in history.data:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            except Exception as e:
                print(f"Error loading history: {e}")

        # Add current message
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

        # Store in Supabase
        if SUPABASE_ENABLED:
            try:
                # Get conversation UUID for foreign key
                conv_result = supabase.table("conversations").select("id").eq(
                    "conversation_id", conversation_id
                ).execute()
                conversation_uuid = conv_result.data[0]['id'] if conv_result.data else None

                # Store user message
                supabase.table("messages").insert({
                    "conversation_id": conversation_id,
                    "conversation_uuid": conversation_uuid,
                    "user_id": user_uuid,
                    "loveable_user_id": chat_message.loveable_user_id,
                    "role": "user",
                    "content": chat_message.message,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()

                # Store assistant message
                supabase.table("messages").insert({
                    "conversation_id": conversation_id,
                    "conversation_uuid": conversation_uuid,
                    "user_id": user_uuid,
                    "loveable_user_id": chat_message.loveable_user_id,
                    "role": "assistant",
                    "content": response,
                    "model": model,
                    "tokens_used": tokens,
                    "sources_used": sources_used,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()

                # Update conversation title if this is the first message
                try:
                    msg_count = supabase.table("messages").select("id").eq(
                        "conversation_id", conversation_id
                    ).execute()

                    if len(msg_count.data) == 2:  # First user + assistant message
                        # Generate title from first message (first 50 chars)
                        title = chat_message.message[:50] + ("..." if len(chat_message.message) > 50 else "")
                        update_conversation_title(conversation_id, title)
                except Exception as e:
                    print(f"Error updating conversation title: {e}")

            except Exception as e:
                print(f"Error storing messages: {e}")

        return ChatResponse(
            response=response,
            conversation_id=conversation_id,
            model_used=model,
            tokens_used=tokens,
            sources_used=sources_used
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
async def chat_stream(chat_message: ChatMessage):
    """Streaming chat endpoint - returns word by word"""
    async def generate():
        try:
            model = chat_message.model or DEFAULT_MODEL

            # Build system prompt with business context if provided
            system_prompt = SYSTEM_PROMPT
            if chat_message.business_context:
                system_prompt += f"\n\n**IMPORTANT - USER'S BUSINESS CONTEXT:**\nAlways reference and use this information when giving advice. Tailor all responses to their specific situation.\n{chat_message.business_context}"

            messages = [{"role": "system", "content": system_prompt}]
            sources_used = []

            # Search Pinecone for context
            if chat_message.use_rag and PINECONE_ENABLED:
                context, sources = search_pinecone(chat_message.message, top_k=3)
                if context:
                    messages.append({"role": "system", "content": context})
                    sources_used = sources

            # Get conversation history from Supabase
            if chat_message.conversation_id and SUPABASE_ENABLED:
                try:
                    history = supabase.table("messages").select("*").eq(
                        "conversation_id", chat_message.conversation_id
                    ).order("created_at").limit(10).execute()

                    for msg in history.data:
                        messages.append({"role": msg["role"], "content": msg["content"]})
                except:
                    pass

            # Add current message
            messages.append({"role": "user", "content": chat_message.message})

            # Call AI with streaming
            stream = ai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                stream=True
            )

            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield f"data: {content}\n\n"

            # Send done signal
            yield "data: [DONE]\n\n"

            # Store in Supabase after completion
            conversation_id = chat_message.conversation_id or f"conv_{datetime.utcnow().timestamp()}"
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
                        "content": full_response,
                        "model": model,
                        "created_at": datetime.utcnow().isoformat()
                    }).execute()
                except:
                    pass

        except Exception as e:
            yield f"data: Error: {str(e)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/api/history/{conversation_id}")
async def get_history(conversation_id: str):
    """Get conversation history"""
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Chat history not available")

    try:
        history = supabase.table("messages").select("*").eq(
            "conversation_id", conversation_id
        ).order("created_at").execute()

        return {"conversation_id": conversation_id, "messages": history.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{loveable_user_id}/conversations")
async def get_user_conversations(loveable_user_id: str):
    """Get all conversations for a specific user"""
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        conversations = supabase.table("conversations").select("*").eq(
            "loveable_user_id", loveable_user_id
        ).order("updated_at", desc=True).execute()

        return {
            "loveable_user_id": loveable_user_id,
            "conversations": conversations.data,
            "count": len(conversations.data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations/{conversation_id}")
async def get_conversation_details(conversation_id: str):
    """Get conversation details with full message history"""
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        # Get conversation metadata
        conv = supabase.table("conversations").select("*").eq(
            "conversation_id", conversation_id
        ).execute()

        if not conv.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get messages
        messages = supabase.table("messages").select("*").eq(
            "conversation_id", conversation_id
        ).order("created_at").execute()

        return {
            "conversation": conv.data[0],
            "messages": messages.data,
            "message_count": len(messages.data)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation and all its messages"""
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        # Delete messages first (will be handled by CASCADE, but being explicit)
        supabase.table("messages").delete().eq("conversation_id", conversation_id).execute()

        # Delete conversation
        supabase.table("conversations").delete().eq("conversation_id", conversation_id).execute()

        return {"message": "Conversation deleted successfully", "conversation_id": conversation_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{loveable_user_id}")
async def get_user_profile(loveable_user_id: str):
    """Get user profile and statistics"""
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        # Get user
        user = supabase.table("users").select("*").eq(
            "loveable_user_id", loveable_user_id
        ).execute()

        if not user.data:
            raise HTTPException(status_code=404, detail="User not found")

        # Get conversation count
        conversations = supabase.table("conversations").select("id").eq(
            "loveable_user_id", loveable_user_id
        ).execute()

        # Get message count
        messages = supabase.table("messages").select("id").eq(
            "loveable_user_id", loveable_user_id
        ).execute()

        return {
            "user": user.data[0],
            "stats": {
                "conversation_count": len(conversations.data),
                "message_count": len(messages.data)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print("🚀 Starting UCX AI Chatbot with Pinecone RAG...")
    print(f"🤖 AI Provider: {AI_PROVIDER}")
    print(f"📚 Pinecone RAG: {'Enabled' if PINECONE_ENABLED else 'Disabled (configure PINECONE_API_KEY)'}")
    print(f"💬 Chat History: {'Enabled' if SUPABASE_ENABLED else 'Disabled'}")
    uvicorn.run(app, host="0.0.0.0", port=port)
