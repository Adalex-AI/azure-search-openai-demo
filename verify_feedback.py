import asyncio
import sys
import os

# Add app/backend to sys.path so we can import app
sys.path.append(os.path.join(os.getcwd(), "app", "backend"))

from app import create_app

async def run_test():
    print("Initializing app...")
    app = create_app()
    test_client = app.test_client()
    
    payload = {
        "message_id": "msg-test-123",
        "rating": "unhelpful",
        "issues": ["wrong_citation", "outdated"],
        "comment": "Test comment from verification script."
    }
    
    print(f"Sending POST request to /api/feedback with payload: {payload}")
    response = await test_client.post("/api/feedback", json=payload)
    
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        data = await response.get_json()
        print(f"Response body: {data}")
        if data.get("status") == "received":
            print("SUCCESS: Feedback endpoint is working correctly.")
        else:
            print("FAILURE: Unexpected response body.")
    else:
        print("FAILURE: Endpoint returned non-200 status code.")

if __name__ == "__main__":
    asyncio.run(run_test())
