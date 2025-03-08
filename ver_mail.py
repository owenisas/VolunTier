import resend

resend.api_key = "re_FcHh1yZ4_NjgDaVXGA9DXmySvuGRLEUHT"
domain_name = "http://127.0.0.1:8000"


def send_verification_email(user_email: str, token: str):
    verification_link = f"http://yourdomain.com/verify?token={token}"
    params: resend.Emails.SendParams = {
        "from": "DO NOT REPLY! <verify@volun-tier.com>",
        "to": user_email,
        "subject": "Please Click this Link below to verify your email, The Link is valid for 10 minutes",
        "html": f"Click <a href='{verification_link}'>here</a> to verify your email."
    }

    email = resend.Emails.send(params)
    return email
