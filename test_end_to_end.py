#!/usr/bin/env python3
"""
End-to-end test: Test connection then save configuration
"""

import requests

def test_end_to_end():
    """Test complete flow: login -> test connection -> save settings"""
    base_url = "http://localhost:8000"
    
    print("End-to-End Test: Connection + Save")
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
    
    # Step 2: Test LLM connection with valid key
    print("\n2. Testing LLM Connection with VALID API Key:")
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
            print("SUCCESS: Connection test passed!")
        else:
            print(f"FAILED: Connection test - {data}")
            return
    except Exception as e:
        print(f"ERROR: {e}")
        return
    
    # Step 3: Save LLM settings
    print("\n3. Saving LLM Settings:")
    try:
        save_payload = {
            "provider": "groq",
            "api_key": "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"
        }
        response = requests.post(f"{base_url}/api/v1/llm/settings", json=save_payload, headers=headers)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if response.status_code == 200:
            print("SUCCESS: Settings saved!")
        else:
            print(f"FAILED: Save settings - {data}")
    except Exception as e:
        print(f"ERROR: {e}")
        return
    
    # Step 4: Load saved settings to verify
    print("\n4. Loading Saved Settings:")
    try:
        response = requests.get(f"{base_url}/api/v1/llm/settings", headers=headers)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if response.status_code == 200:
            print("SUCCESS: Settings loaded and verified!")
        else:
            print(f"FAILED: Load settings - {data}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_end_to_end()
