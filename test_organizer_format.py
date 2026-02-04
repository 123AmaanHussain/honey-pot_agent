# Test Organizer Format
import requests
import json

# Test data matching organizer's format
test_data = {
    "sessionId": "wertyu-dfghj-ertyui",
    "message": {
        "sender": "scammer",
        "text": "Your bank account will be blocked today. Verify immediately.",
        "timestamp": 1770005528731
    },
    "conversationHistory": [],
    "metadata": {
        "channel": "SMS",
        "language": "English",
        "locale": "IN"
    }
}

# Test locally
response = requests.post(
    "http://localhost:8000/honeypot/message",
    headers={
        "x-api-key": "test_secret_key_12345",
        "Content-Type": "application/json"
    },
    json=test_data
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
