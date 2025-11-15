#!/usr/bin/env python3
"""
Complete system test - verifies DeepSeek + Supabase integration
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client
import json

load_dotenv()

def test_env_vars():
    """Check if all environment variables are set"""
    print("=" * 60)
    print("🔍 Step 1: Checking Environment Variables")
    print("=" * 60)

    required_vars = {
        "AI_PROVIDER": os.getenv("AI_PROVIDER"),
        "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY"),
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY"),
    }

    all_set = True
    for var, value in required_vars.items():
        if value and "your_" not in value:
            print(f"✅ {var}: {value[:30]}...")
        else:
            print(f"❌ {var}: NOT SET")
            all_set = False

    print()
    return all_set

def test_supabase():
    """Test Supabase connection"""
    print("=" * 60)
    print("🗄️  Step 2: Testing Supabase Connection")
    print("=" * 60)

    try:
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )

        # Try to query the messages table
        response = supabase.table("messages").select("*").limit(1).execute()

        print(f"✅ Connected to Supabase!")
        print(f"✅ 'messages' table exists")
        print(f"📊 Current messages in DB: {len(response.data)}")
        print()
        return True

    except Exception as e:
        print(f"❌ Supabase Error: {e}")
        print()
        print("💡 Did you run the SQL schema?")
        print("   1. Go to https://xqkaioydgtlyfmwjvyhg.supabase.co")
        print("   2. Click 'SQL Editor' in the left sidebar")
        print("   3. Copy contents of 'supabase_schema.sql'")
        print("   4. Paste and click 'Run'")
        print()
        return False

def test_deepseek():
    """Test DeepSeek API"""
    print("=" * 60)
    print("🤖 Step 3: Testing DeepSeek API")
    print("=" * 60)

    try:
        client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

        print("📡 Sending test message...")

        completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello from DeepSeek!' in one sentence."}
            ],
            temperature=0.7,
            max_tokens=50
        )

        response = completion.choices[0].message.content
        tokens = completion.usage.total_tokens
        cost = (tokens / 1000000) * 0.14

        print(f"✅ DeepSeek is working!")
        print(f"🤖 Response: {response}")
        print(f"📊 Tokens: {tokens} | Cost: ${cost:.6f}")
        print()
        return True

    except Exception as e:
        print(f"❌ DeepSeek Error: {e}")
        print()
        return False

def test_full_flow():
    """Test complete chat flow with database storage"""
    print("=" * 60)
    print("🚀 Step 4: Testing Complete Chat Flow")
    print("=" * 60)

    try:
        # Initialize clients
        ai_client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )

        from datetime import datetime
        conversation_id = f"test_{datetime.utcnow().timestamp()}"

        print(f"💬 Conversation ID: {conversation_id}")
        print()

        # Send message to DeepSeek
        print("1️⃣ Sending message to DeepSeek...")
        user_message = "What is 2+2? Answer in one short sentence."

        completion = ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=50
        )

        assistant_response = completion.choices[0].message.content
        tokens = completion.usage.total_tokens

        print(f"   User: {user_message}")
        print(f"   AI: {assistant_response}")
        print()

        # Store in Supabase
        print("2️⃣ Storing in Supabase...")

        # Store user message
        supabase.table("messages").insert({
            "conversation_id": conversation_id,
            "user_id": "test_user",
            "role": "user",
            "content": user_message,
            "created_at": datetime.utcnow().isoformat()
        }).execute()

        # Store assistant message
        supabase.table("messages").insert({
            "conversation_id": conversation_id,
            "user_id": "test_user",
            "role": "assistant",
            "content": assistant_response,
            "model": "deepseek-chat",
            "tokens_used": tokens,
            "created_at": datetime.utcnow().isoformat()
        }).execute()

        print(f"   ✅ Messages stored in database")
        print()

        # Retrieve from Supabase
        print("3️⃣ Retrieving from Supabase...")

        history = supabase.table("messages").select("*").eq(
            "conversation_id", conversation_id
        ).order("created_at").execute()

        print(f"   ✅ Retrieved {len(history.data)} messages")
        for msg in history.data:
            print(f"   - {msg['role']}: {msg['content'][:50]}...")
        print()

        # Clean up test data
        print("4️⃣ Cleaning up test data...")
        supabase.table("messages").delete().eq(
            "conversation_id", conversation_id
        ).execute()
        print(f"   ✅ Test data cleaned up")
        print()

        return True

    except Exception as e:
        print(f"❌ Full Flow Error: {e}")
        print()
        return False

def main():
    print()
    print("🧪 UCX AI CHATBOT - COMPLETE SYSTEM TEST")
    print()

    results = {
        "Environment Variables": test_env_vars(),
        "Supabase Connection": test_supabase(),
        "DeepSeek API": test_deepseek(),
        "Complete Flow": test_full_flow()
    }

    print("=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)

    for test, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test:.<40} {status}")

    print()

    if all(results.values()):
        print("🎉 ALL TESTS PASSED! Your chatbot is ready to go!")
        print()
        print("Next steps:")
        print("1. Run the server: python main.py")
        print("2. Test the API: curl -X POST http://localhost:8000/api/chat \\")
        print("                      -H 'Content-Type: application/json' \\")
        print("                      -d '{\"message\": \"Hello!\"}'")
        print("3. Deploy to production (Railway/Render)")
        print("4. Embed in your Lovable website")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")

    print()

if __name__ == "__main__":
    main()
