import os
import requests
import json
from pathlib import Path

def test_endpoint():
    # Get API key from environment
    api_key = os.environ.get("APPLIO_API_WRITE")

    # Request data
    data = {
        "text": "Welcome to Applio, your voice AI platform",
        "voice": "en-US-GuyNeural"
    }

    # Headers
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }

    # Test endpoints
    endpoints = [
        ("Local", "http://localhost:8080/api/tts-rvc"),
        ("Tunnel", "https://docker-api-test-app-tunnel-b9j2vimp.devinapps.com/api/tts-rvc")
    ]

    for name, url in endpoints:
        print(f"\nTesting {name} endpoint: {url}")
        try:
            # For tunnel endpoint, add basic auth
            auth = ("user", "357d758cab4ccaeb5e6b4bab71a1237c") if "tunnel" in url.lower() else None

            # Make request with SSL verification disabled for tunnel
            verify = False if "tunnel" in url.lower() else True
            response = requests.post(url, json=data, headers=headers, auth=auth, verify=verify)

            print(f"Status Code: {response.status_code}")
            print("Response:")
            print(json.dumps(response.json(), indent=2))

            # Check if WAV file was generated
            if response.status_code == 200:
                result = response.json()
                audio_path = result.get("audio_path")
                if audio_path and Path(audio_path).exists():
                    print(f"WAV file generated successfully at: {audio_path}")
                    print(f"File size: {Path(audio_path).stat().st_size} bytes")
                else:
                    print(f"Warning: WAV file not found at {audio_path}")

        except Exception as e:
            print(f"Error testing {name} endpoint: {str(e)}")
            continue

if __name__ == "__main__":
    test_endpoint()
