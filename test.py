import requests
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000"

def test_register():
    url = f"{BASE_URL}/register"
    user_data = {
        "username": "testuserkokokk",
        "email": "justcs123only@gmail.com",
        "password": "testpassword",  # In production, use hashed passwords.
        "full_name": "Test User",
        "profile": "This is a test profile",
        "age": 25
    }
    response = requests.post(url, json=user_data)
    print("Register:", response.status_code, response.json())
    return response.json()

def test_login():
    url = f"{BASE_URL}/login"
    login_data = {
        "email": "justcs123only@gmail.com",
        "password": "testpassword"
    }
    response = requests.post(url, json=login_data)
    print("Login:", response.status_code, response.json())
    token = response.json().get("access_token")
    return token

def test_create_event(token):
    url = f"{BASE_URL}/events/create"
    headers = {"Authorization": f"Bearer {token}"}
    # Set event time to current UTC time plus 10 minutes (ISO 8601 formatted)
    event_time = (datetime.utcnow() + timedelta(minutes=1000)).isoformat()
    event_data = {
        "title": "Test Event",
        "details": "This is a test event",
        "time": event_time,
        "picture": "http://example.com/image.png",
        "event_link": "http://example.com",
        "location": "Test Location",
        "certificate": 1,
        "requirements": "None",
        "contact_methods": "email",
        "instructions": "Test instructions",
        "max_participants": 100,
        "duration": 60,       # Duration in minutes
        "status": True        # True means upcoming/active
    }
    response = requests.post(url, json=event_data, headers=headers)
    try:
        data = response.json()
    except Exception as e:
        print("Create Event: Failed to decode JSON. Response text:", response.text)
        raise e
    print("Create Event:", response.status_code, data)
    return data

def test_join_event(event_id, token):
    url = f"{BASE_URL}/events/{event_id}/join"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers)
    print("Join Event:", response.status_code, response.json())

def test_get_user(user_id):
    url = f"{BASE_URL}/users/{user_id}"
    response = requests.get(url)
    print("Get User:", response.status_code, response.json())

def test_get_event(event_id):
    url = f"{BASE_URL}/events/{event_id}"
    response = requests.get(url)
    print("Get Event:", response.status_code, response.json())

if __name__ == "__main__":
    # Register the user and capture token from registration response.
    reg_response = test_register()
    user = reg_response.get("user")
    print(user)
    token = test_login()
    user_id = 1
    # Since we already have a token from registration, no need to login again.
    # Create an event (user provides a start time in 'time')
    event = test_create_event(token)
    event_id = event.get("event_id")
    # Attempt to join the event.
    test_join_event(event_id, token)
    # Get user info.
    test_get_user(user_id)
    # Get event info.
    test_get_event(event_id)
