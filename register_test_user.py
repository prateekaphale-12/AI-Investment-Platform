#!/usr/bin/env python3
"""
Register a new test user for testing
"""

import requests

def register_test_user():
    """Register a new test user"""
    base_url = "http://localhost:8000"
    
    print("Registering New Test User...")
    print("=" * 50)
    
    try:
        # Generate unique email with timestamp
        import time
        timestamp = int(time.time())
        test_email = f"testuser{timestamp}@example.com"
        
        register_payload = {
            "email": test_email,
            "password": "test123456"
        }
        
        response = requests.post(f"{base_url}/api/v1/auth/register", json=register_payload)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if response.status_code == 200:
            token = data.get("access_token")
            print(f"✅ SUCCESS!")
            print(f"Email: {test_email}")
            print(f"Token: {token[:50]}...")
            return test_email, token
        else:
            print(f"❌ FAILED: {data}")
            return None, None
            
    except Exception as e:
        print(f"ERROR: {e}")
        return None, None

if __name__ == "__main__":
    register_test_user()
