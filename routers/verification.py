# routers/verification.py
from fastapi import APIRouter, Depends, HTTPException, Query
from database import get_db
import sqlite3
import jwt
from config import SECRET_KEY, ALGORITHM

router = APIRouter()

FREE_EMAIL_PROVIDERS = {
    "gmail.com", "yahoo.com", "hotmail.com",
    "outlook.com", "icloud.com", "aol.com",
    "protonmail.com"
}


@router.get("/verify")
def verify_email(
        token: str,
        email: str = Query(...),
        db: sqlite3.Connection = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=400, detail="Invalid token payload")
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid token")

    cursor = db.cursor()
    cursor.execute(
        "UPDATE Users SET verified_email = ? WHERE user_id = ?",
        (email, user_id)
    )
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")
    db.commit()

    return {"message": "Email verified successfully."}


@router.get("/verify/edu")
def verify_edu_email(
        token: str,
        email: str = Query(...),
        db: sqlite3.Connection = Depends(get_db)
):
    # decode and validate token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(400, "Invalid token payload")
    except jwt.PyJWTError:
        raise HTTPException(400, "Invalid token")

    # enforce .edu address
    if not email.lower().endswith(".edu"):
        raise HTTPException(400, "Email is not a valid .edu address")

    # update database
    cursor = db.cursor()
    cursor.execute(
        "UPDATE Users SET edu_verification_email = ? WHERE user_id = ?",
        (email, user_id)
    )
    if cursor.rowcount == 0:
        raise HTTPException(404, "User not found")
    db.commit()

    return {"message": "Education email verified successfully."}


@router.get("/verify/work")
def verify_work_email(
        token: str,
        email: str = Query(...),
        db: sqlite3.Connection = Depends(get_db)
):
    # decode and validate token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(400, "Invalid token payload")
    except jwt.PyJWTError:
        raise HTTPException(400, "Invalid token")

    # enforce corporate (non-public) email domain
    domain = email.split("@")[-1].lower()
    if domain in FREE_EMAIL_PROVIDERS or domain.endswith(".edu"):
        raise HTTPException(400, "Email is not a valid corporate address")

    # update database
    cursor = db.cursor()
    cursor.execute(
        "UPDATE Users SET work_verification_email = ? WHERE user_id = ?",
        (email, user_id)
    )
    if cursor.rowcount == 0:
        raise HTTPException(404, "User not found")
    db.commit()

    return {"message": "Work email verified successfully."}
