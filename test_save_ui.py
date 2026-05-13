#!/usr/bin/env python3
"""
Test save button functionality and UI feedback
"""

import requests

def test_save_ui():
    """Test save functionality and check if UI should show success message"""
    base_url = "http://localhost:8000"
    
    print("Testing Save Button UI Feedback")
    print("=" * 50)
    
    # Step 1: Login
    print("\n1. Logging in:")
    try:
        login_payload = {
            "email": "testuser1778495188@example.com",
            "password": "test123456"
        }
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_payload)
        if response.status_code == 200:
            token = response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Login successful")
        else:
            print("❌ Login failed")
            return
    except Exception as e:
        print(f"ERROR: {e}")
        return
    
    # Step 2: Test save with valid data
    print("\n2. Testing Save with Valid API Key:")
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
            print("✅ Save successful - UI should show success message")
        else:
            print(f"❌ Save failed: {data}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Step 3: Verify saved data
    print("\n3. Verifying Saved Data:")
    try:
        response = requests.get(f"{base_url}/api/v1/llm/settings", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Loaded settings: {data}")
            if data.get('has_api_key'):
                print("✅ Data saved correctly")
            else:
                print("❌ Data not saved")
        else:
            print(f"❌ Load failed: {response.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_save_ui()
