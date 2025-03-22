
import requests


BASE_URL = "http://127.0.0.1:8000"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzQyNjc5OTkyfQ.CaBqw9IOz8K72pnwL1nGiwdOGeakjblKhsHFvViRrdU"
url = f"{BASE_URL}/events/1"
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(url)
print("Get Event:", response.status_code, response.json())