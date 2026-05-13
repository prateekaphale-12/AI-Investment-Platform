#!/usr/bin/env python3
"""
Test LLM connection with new registered user
"""

import requests
import json

def test_llm_with_new_user():
    """Test LLM connection with new user"""
    base_url = "http://localhost:8000"
    
    print("Testing LLM Connection with New User...")
    print("=" * 50)
    
    # Step 1: Login with new user
    print("\n1. Logging in with new user:")
    try:
        login_payload = {
            "email": "testuser1778495188@example.com",
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
    
    # Step 2: Test LLM connection with auth
    print("\n2. Testing LLM Connection with Auth:")
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
            print("SUCCESS: LLM Test PASSED!")
        else:
            print(f"FAILED: LLM Test - {data}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_llm_with_new_user()
