#!/usr/bin/env python3
"""Quick test for Groq API"""

from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

print("🧪 Testing Groq API...")
print()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

try:
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # Updated Groq model
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Groq is working!' in a fun way."}
        ],
        temperature=0.7,
        max_tokens=100
    )

    response = completion.choices[0].message.content
    tokens = completion.usage.total_tokens

    print("✅ SUCCESS! Groq is working!\n")
    print(f"🤖 Response: {response}")
    print(f"📊 Tokens used: {tokens}")
    print(f"💰 Cost: $0.00 (FREE!)")
    print(f"⚡ Model: llama-3.1-70b-versatile")
    print()
    print("🎉 Your chatbot is ready to go!")
    print()
    print("Next step: Run 'python main.py' to start your API server!")

except Exception as e:
    print(f"❌ Error: {e}")
