#!/usr/bin/env python3
"""
Quick test script to verify DeepSeek API is working
Run this before setting up Supabase to test the AI connection
"""

from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

def test_deepseek():
    print("🧪 Testing DeepSeek API connection...")

    # Check if API key is loaded
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key or api_key == "your_deepseek_api_key_here":
        print("❌ Error: DEEPSEEK_API_KEY not found in .env")
        return False

    print(f"✅ API key found: {api_key[:20]}...")

    # Test the API
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        print("📡 Sending test message to DeepSeek...")

        completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello! DeepSeek is working!' in a fun way."}
            ],
            temperature=0.7,
            max_tokens=100
        )

        response = completion.choices[0].message.content
        tokens = completion.usage.total_tokens

        print(f"\n✅ SUCCESS! DeepSeek is working!\n")
        print(f"🤖 Response: {response}")
        print(f"📊 Tokens used: {tokens}")
        print(f"💰 Cost: ${(tokens / 1000000) * 0.14:.6f}")

        return True

    except Exception as e:
        print(f"\n❌ Error testing DeepSeek API: {e}")
        return False

if __name__ == "__main__":
    test_deepseek()
