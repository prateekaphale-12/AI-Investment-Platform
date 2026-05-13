#!/usr/bin/env python3
"""
Test backend Groq connection directly
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from groq import AsyncGroq

# User's provided API key
USER_API_KEY = "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"

async def test_backend_groq():
    """Test Groq exactly like backend should work"""
    print("Testing Backend Groq Implementation...")
    print(f"API Key: {USER_API_KEY[:20]}...")
    print("-" * 50)
    
    try:
        # Initialize client exactly like standalone test
        client = AsyncGroq(api_key=USER_API_KEY)
        print("Client initialized successfully")
        
        # Test 1: Simple completion
        print("\nTest 1: Simple Math (2+2)")
        start_time = asyncio.get_event_loop().time()
        
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": "What is 2+2? Answer with just the number."}
            ],
            max_tokens=10,
            temperature=0.1
        )
        
        end_time = asyncio.get_event_loop().time()
        latency = (end_time - start_time) * 1000
        
        result = response.choices[0].message.content.strip()
        print(f"Response: '{result}'")
        print(f"Latency: {latency:.0f}ms")
        
        if result == "4":
            print("SUCCESS: Backend test works!")
            return {"success": True, "response": result, "provider": "groq"}
        else:
            print(f"ERROR: Expected '4', got '{result}'")
            return {"success": False, "error": f"Wrong response: {result}", "provider": "groq"}
            
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return {"success": False, "error": str(e), "provider": "groq"}

if __name__ == "__main__":
    print("Backend Groq Test")
    print("=" * 50)
    result = asyncio.run(test_backend_groq())
    print(f"\nFinal Result: {result}")
