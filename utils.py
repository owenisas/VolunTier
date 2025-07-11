# utils.py
from datetime import datetime, timedelta
import jwt
import requests
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, RESEND_API_KEY, BASE_DOMAIN

def create_access_token(subject: str, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    expire = datetime.utcnow() + expires_delta
    token_data = {"sub": subject, "exp": expire}
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

def create_verification_token(user_id: int):
    # Token valid for 24 hours
    expire = datetime.utcnow() + timedelta(hours=24)
    token_data = {"sub": str(user_id), "exp": expire}
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

def create_image_url(filename: str, folder: str, expires_minutes=1440):
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload = {
        "filename": filename,
        "folder": folder,
        "exp": expire
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    secure_url = f"http://app.volun-tier.com/images/{token}"
    return secure_url

def decode_image_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # Contains 'filename' and 'folder'
    except jwt.ExpiredSignatureError:
        raise Exception("URL Expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid Token")


import resend

resend.api_key = "re_FcHh1yZ4_NjgDaVXGA9DXmySvuGRLEUHT"
domain_name = "http://app.volun-tier.com"


def send_verification_email(user_email: str, token: str):
    verification_link = f"{domain_name}/verify?token={token}&email={user_email}"
    params: resend.Emails.SendParams = {
        "from": "DO NOT REPLY! <verify@volun-tier.com>",
        "to": user_email,
        "subject": "Please Click this Link below to verify your email, The Link is valid for 10 minutes",
        "html": f"Click <a href='{verification_link}'>here</a> to verify your email."
    }

    email = resend.Emails.send(params)
    return email
