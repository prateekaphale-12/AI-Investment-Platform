#!/usr/bin/env python3
"""
Test the user's provided Groq API key
"""

import asyncio
import time
from groq import AsyncGroq

# User's provided API key
USER_API_KEY = "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"

async def test_user_key():
    """Test the user's specific API key"""
    print("Testing User's Groq API Key...")
    print(f"API Key: {USER_API_KEY[:20]}...")
    print("-" * 50)
    
    try:
        # Initialize client with user's key
        client = AsyncGroq(api_key=USER_API_KEY)
        print("Client initialized successfully")
        
        # Test 1: Simple completion
        print("\nTest 1: Simple Math (2+2)")
        start_time = time.time()
        
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": "What is 2+2? Answer with just the number."}
            ],
            max_tokens=10,
            temperature=0.1
        )
        
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        
        print(f"Response: '{response.choices[0].message.content.strip()}'")
        print(f"Latency: {latency:.0f}ms")
        print(f"Usage: {response.usage}")
        
        # Test 2: Check if response is correct
        if response.choices[0].message.content.strip() == "4":
            print("CORRECT: API key works properly!")
        else:
            print(f"INCORRECT: Expected '4', got '{response.choices[0].message.content.strip()}'")
            
        # Test 3: Investment style
        print("\nTest 2: Investment Analysis")
        start_time = time.time()
        
        investment_prompt = "Briefly analyze AAPL at $175.50 with RSI 65.2. 2 sentences max."
        
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": investment_prompt}
            ],
            max_tokens=100,
            temperature=0.4
        )
        
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        
        print(f"Response: {response.choices[0].message.content.strip()}")
        print(f"Latency: {latency:.0f}ms")
        print(f"Usage: {response.usage}")
        
        print("\n" + "=" * 50)
        print("API KEY VERIFICATION COMPLETE!")
        print("User's API key is VALID and WORKING!")
        print("The issue is in the backend implementation, not the key!")
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        print("\nKey Issues:")
        print("1. Check if key is exactly as provided")
        print("2. Verify no extra spaces or characters")
        print("3. Check if Groq service is available")
        print("4. Verify model name: llama-3.1-8b-instant")

if __name__ == "__main__":
    print("User API Key Verification")
    print("=" * 50)
    asyncio.run(test_user_key())
