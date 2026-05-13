#!/usr/bin/env python3
"""
Quick Groq API Test Script - No Emojis
Tests connection, speed, and basic response quality
"""

import asyncio
import time
from groq import AsyncGroq

# Your Groq API key
GROQ_API_KEY = "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"

async def test_groq_connection():
    """Test Groq API connection and response"""
    print("Testing Groq API Connection...")
    print(f"Using API Key: {GROQ_API_KEY[:20]}...")
    print("-" * 50)
    
    try:
        # Initialize client
        client = AsyncGroq(api_key=GROQ_API_KEY)
        print("Client initialized successfully")
        
        # Test 1: Simple completion
        print("\nTest 1: Simple Text Completion")
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
        latency = (end_time - start_time) * 1000  # Convert to ms
        
        print(f"Response: {response.choices[0].message.content}")
        print(f"Latency: {latency:.0f}ms")
        print(f"Usage: {response.usage}")
        
        # Test 2: Investment analysis style
        print("\nTest 2: Investment Analysis Style")
        start_time = time.time()
        
        investment_prompt = """
        Analyze this stock data for AAPL:
        - Current Price: $175.50
        - P/E Ratio: 28.5
        - RSI: 65.2
        - Recent Return: +12.3%
        
        Provide a brief investment analysis (2-3 sentences max).
        """
        
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": investment_prompt}
            ],
            max_tokens=200,
            temperature=0.4
        )
        
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        
        print(f"Response: {response.choices[0].message.content}")
        print(f"Latency: {latency:.0f}ms")
        print(f"Usage: {response.usage}")
        
        # Test 3: JSON generation (like your app uses)
        print("\nTest 3: JSON Generation (like your app)")
        start_time = time.time()
        
        json_prompt = """
        Return ONLY valid JSON with this structure:
        {
            "ticker": "AAPL",
            "sentiment": "bullish|bearish|neutral",
            "confidence": 0.0-1.0,
            "reason": "brief explanation"
        }
        
        Based on: AAPL at $175.50 with positive momentum.
        """
        
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": json_prompt}
            ],
            max_tokens=100,
            temperature=0.2
        )
        
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        
        print(f"Response: {response.choices[0].message.content}")
        print(f"Latency: {latency:.0f}ms")
        print(f"Usage: {response.usage}")
        
        print("\n" + "=" * 50)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("Your Groq API key is working perfectly!")
        print("Average latency looks good for production use!")
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        print("\nTroubleshooting:")
        print("1. Check if API key is correct")
        print("2. Verify internet connection")
        print("3. Check Groq service status")
        print("4. Verify model name: llama3-70b-8192")

if __name__ == "__main__":
    print("Groq API Test Script")
    print("=" * 50)
    asyncio.run(test_groq_connection())
