#!/usr/bin/env python3
"""
Test backend endpoints directly
"""

import requests
import json

def test_backend():
    """Test backend endpoints"""
    base_url = "http://localhost:8000"
    
    print("Testing Backend Endpoints...")
    print("=" * 50)
    
    # Test 1: Health endpoint
    print("\n1. Testing Health Endpoint:")
    try:
        response = requests.get(f"{base_url}/api/v1/health")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 2: LLM providers endpoint
    print("\n2. Testing LLM Providers Endpoint:")
    try:
        response = requests.get(f"{base_url}/api/v1/llm/providers")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 3: LLM test endpoint (without auth first)
    print("\n3. Testing LLM Test Endpoint (No Auth):")
    try:
        payload = {
            "provider": "groq",
            "api_key": "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"
        }
        response = requests.post(f"{base_url}/api/v1/llm/test", json=payload)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_backend()
