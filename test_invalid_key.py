#!/usr/bin/env python3
"""
Test error handling with invalid API key
"""

import requests

def test_invalid_key():
    """Test LLM connection with invalid API key"""
    base_url = "http://localhost:8000"
    
    print("Testing Invalid API Key Handling...")
    print("=" * 50)
    
    # Step 1: Login to get token
    print("\n1. Logging in with test user:")
    try:
        login_payload = {
            "email": "testuser1778495188@example.com",
            "password": "test123456"
        }
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_payload)
        print(f"Status: {response.status_code}")
        data = response.json()
        
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
    
    # Step 2: Test LLM connection with invalid key
    print("\n2. Testing LLM Connection with INVALID API Key:")
    try:
        llm_payload = {
            "provider": "groq",
            "api_key": "invalid_key_test_12345"
        }
        response = requests.post(f"{base_url}/api/v1/llm/test", json=llm_payload, headers=headers)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if response.status_code == 200:
            if data.get("success"):
                print("✅ Test passed")
            else:
                print(f"✅ Error handling worked: {data.get('error')}")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_invalid_key()
