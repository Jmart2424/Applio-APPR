import os
import requests
import json
from pathlib import Path
import urllib3
from requests.exceptions import Timeout, RequestException

# Disable SSL warnings for tunnel endpoint
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_endpoints():
    # Get API key
    api_key = "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"

    # Test configuration
    endpoints = [
        {
            "name": "Local",
            "url": "http://localhost:8080/api/tts-rvc",
            "auth": None,
            "verify": True
        },
        {
            "name": "Tunnel",
            "url": "https://docker-api-test-app-tunnel-b9j2vimp.devinapps.com/api/tts-rvc",
            "auth": ("user", "357d758cab4ccaeb5e6b4bab71a1237c"),
            "verify": False
        }
    ]

    # Request data
    data = {
        "text": "Welcome to Applio, your voice AI platform",
        "voice": "en-US-GuyNeural"
    }

    for endpoint in endpoints:
        print(f"\nTesting {endpoint['name']} endpoint: {endpoint['url']}")

        headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }

        try:
            print("Sending request...")
            response = requests.post(
                endpoint["url"],
                json=data,
                headers=headers,
                auth=endpoint["auth"],
                verify=endpoint["verify"],
                timeout=30  # 30 second timeout
            )

            print(f"Status Code: {response.status_code}")
            print("Response Headers:", json.dumps(dict(response.headers), indent=2))

            try:
                response_json = response.json()
                print("Response Body:", json.dumps(response_json, indent=2))

                if response.status_code == 200:
                    audio_path = response_json.get("audio_path")
                    if audio_path and Path(audio_path).exists():
                        print(f"WAV file generated successfully at: {audio_path}")
                        print(f"File size: {Path(audio_path).stat().st_size} bytes")
                    else:
                        print(f"Warning: WAV file not found at {audio_path}")
                else:
                    print(f"Error: Request failed with status code {response.status_code}")
            except json.JSONDecodeError:
                print("Error: Invalid JSON response")
                print("Raw response:", response.text[:500])

        except Timeout:
            print(f"Error: Request to {endpoint['name']} endpoint timed out after 30 seconds")
        except RequestException as e:
            print(f"Error testing {endpoint['name']} endpoint: {str(e)}")
        except Exception as e:
            print(f"Unexpected error testing {endpoint['name']} endpoint: {str(e)}")
            continue

if __name__ == "__main__":
    test_endpoints()
