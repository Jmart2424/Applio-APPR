import os
import requests
import json
from pathlib import Path

def debug_auth():
    # Get and verify API key
    api_key = os.environ.get("APPLIO_API_WRITE")
    print(f"API Key length: {len(api_key) if api_key else 0}")
    if api_key:
        print(f"API Key preview: {api_key[:5]}...{api_key[-5:]}")
    else:
        print("Warning: APPLIO_API_WRITE environment variable not set")
        return

    # Test local endpoint
    url = "http://localhost:8080/api/tts-rvc"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    data = {
        "text": "Welcome to Applio, your voice AI platform",
        "voice": "en-US-GuyNeural"
    }

    try:
        print(f"\nTesting endpoint: {url}")
        print("Request Headers:", json.dumps(headers, indent=2))
        print("Request Data:", json.dumps(data, indent=2))
        
        response = requests.post(url, json=data, headers=headers)
        print(f"\nStatus Code: {response.status_code}")
        print("Response Headers:", json.dumps(dict(response.headers), indent=2))
        print("Response Body:", json.dumps(response.json(), indent=2))

        if response.status_code == 200:
            result = response.json()
            audio_path = result.get("audio_path")
            if audio_path and Path(audio_path).exists():
                print(f"\nWAV file generated successfully at: {audio_path}")
                print(f"File size: {Path(audio_path).stat().st_size} bytes")
            else:
                print(f"\nWarning: WAV file not found at {audio_path}")
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    debug_auth()
