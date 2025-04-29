# routers/verification.py
from fastapi import APIRouter, Depends, HTTPException
from database import get_db
import sqlite3
import jwt
from config import SECRET_KEY, ALGORITHM

router = APIRouter()

@router.get("/verify")
def verify_email(token: str, db: sqlite3.Connection = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    cursor = db.cursor()
    cursor.execute("UPDATE Users SET verification = 1 WHERE user_id = ?", (user_id,))
    db.commit()
    return {"message": "Email verified successfully."}
