#!/usr/bin/env python3
"""
Test LLM connection with authentication
"""

import requests
import json

def test_llm_with_auth():
    """Test LLM connection with proper authentication"""
    base_url = "http://localhost:8000"
    
    print("Testing LLM Connection with Auth...")
    print("=" * 50)
    
    # Step 1: Register a test user
    print("\n1. Registering Test User:")
    try:
        register_payload = {
            "email": "test@example.com",
            "password": "test123456"
        }
        response = requests.post(f"{base_url}/api/v1/auth/register", json=register_payload)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if response.status_code == 200:
            token = data.get("access_token")
            print(f"Token: {token[:50]}...")
        else:
            print("User might already exist, trying login...")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Step 2: Login to get token
    print("\n2. Logging In:")
    try:
        login_payload = {
            "email": "test@example.com",
            "password": "test123456"
        }
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_payload)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if response.status_code == 200:
            token = data.get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            print(f"Token: {token[:50]}...")
        else:
            print("Failed to get token")
            return
    except Exception as e:
        print(f"ERROR: {e}")
        return
    
    # Step 3: Test LLM connection with auth
    print("\n3. Testing LLM Connection with Auth:")
    try:
        llm_payload = {
            "provider": "groq",
            "api_key": "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"
        }
        response = requests.post(f"{base_url}/api/v1/llm/test", json=llm_payload, headers=headers)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if response.status_code == 200 and data.get("success"):
            print("✅ LLM Test SUCCESSFUL!")
        else:
            print(f"❌ LLM Test FAILED: {data}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_llm_with_auth()
