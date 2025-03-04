import requests

def send_verification_email(user_email: str, token: str):
    api_key = "re_FcHh1yZ4_NjgDaVXGA9DXmySvuGRLEUHT"  # Replace with your Resend API key
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    # Construct a verification link (adjust the domain as needed)
    verification_link = f"http://yourdomain.com/verify?token={token}"
    data = {
        "from": "noreply@yourdomain.com",
        "to": user_email,
        "subject": "Verify your email",
        "html": f"Click <a href='{verification_link}'>here</a> to verify your email."
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()
