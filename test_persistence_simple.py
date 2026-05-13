#!/usr/bin/env python3
"""
Test complete persistence: Save -> Logout -> Login -> Load
"""

import requests

def test_persistence():
    """Test that settings persist across user sessions"""
    base_url = "http://localhost:8000"
    
    print("Testing Settings Persistence Across User Sessions")
    print("=" * 60)
    
    # Step 1: Login and save settings
    print("\n1. Login and Save Settings:")
    try:
        login_payload = {
            "email": "testuser1778495188@example.com",
            "password": "test123456"
        }
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_payload)
        if response.status_code == 200:
            token1 = response.json().get("access_token")
            headers1 = {"Authorization": f"Bearer {token1}"}
            print("Login successful")
            
            # Save settings
            save_payload = {
                "provider": "groq",
                "api_key": "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"
            }
            response = requests.post(f"{base_url}/api/v1/llm/settings", json=save_payload, headers=headers1)
            if response.status_code == 200:
                print("Settings saved successfully")
            else:
                print(f"Save failed: {response.json()}")
                return
        else:
            print("Login failed")
            return
    except Exception as e:
        print(f"ERROR: {e}")
        return
    
    # Step 2: Simulate logout/login (get new token)
    print("\n2. Simulate Logout/Login (New Session):")
    try:
        # Login again to simulate new session
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_payload)
        if response.status_code == 200:
            token2 = response.json().get("access_token")
            headers2 = {"Authorization": f"Bearer {token2}"}
            print("New login successful")
            
            # Load settings with new token
            response = requests.get(f"{base_url}/api/v1/llm/settings", headers=headers2)
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Response: {data}")
            
            if response.status_code == 200 and data.get('has_api_key'):
                print("SUCCESS: Settings persisted across sessions!")
                print(f"Provider: {data.get('provider')}")
                print(f"Model: {data.get('model')}")
                print(f"Has API Key: {data.get('has_api_key')}")
                return True
            else:
                print("FAILED: Settings did not persist")
                return False
        else:
            print("New login failed")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_persistence()
    print(f"\nFinal Result: {'PASSED' if success else 'FAILED'}")
