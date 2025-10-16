#!/usr/bin/env python3
"""
Test different authentication methods for LightX API
"""

import requests
import json

def test_auth_methods():
    API_KEY = "c87fbbdea28849dabbba313479687776_4bafb2c2689a4569af75e210a8334ace_andoraitools"
    
    print("🔐 Testing LightX Authentication Methods")
    print("=" * 40)
    
    endpoint = "https://api.lightxeditor.com/external/api/v2/ai-expand"
    test_data = {
        "imageUrl": "https://example.com/test.jpg",
        "leftPadding": 0,
        "rightPadding": 0,
        "topPadding": 0,
        "bottomPadding": 0
    }
    
    # Test different authentication methods
    auth_methods = [
        {"x-api-key": API_KEY},
        {"api-key": API_KEY},
        {"Authorization": f"Bearer {API_KEY}"},
        {"Authorization": f"Token {API_KEY}"},
        {"X-API-Key": API_KEY},
        {"X-Api-Key": API_KEY},
        {"apikey": API_KEY},
        {"key": API_KEY}
    ]
    
    for i, headers in enumerate(auth_methods, 1):
        headers["Content-Type"] = "application/json"
        print(f"\n🧪 Method {i}: {list(headers.keys())}")
        try:
            response = requests.post(endpoint, headers=headers, json=test_data)
            print(f"   Status: {response.status_code}")
            if response.status_code != 403:
                print(f"   ✅ Different response!")
                print(f"   Response: {response.text[:200]}")
            else:
                print(f"   ❌ Still 403")
        except Exception as e:
            print(f"   Error: {e}")

if __name__ == "__main__":
    test_auth_methods()
