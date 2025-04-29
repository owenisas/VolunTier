# auth.py
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import sqlite3
import jwt
from config import SECRET_KEY, ALGORITHM
from database import get_db
from typing import Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)

def get_current_user(token: str = Depends(oauth2_scheme), db: sqlite3.Connection = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)

def get_current_user_optional(token: Optional[str] = Depends(optional_oauth2_scheme), db: sqlite3.Connection = Depends(get_db)) -> Optional[dict]:
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except Exception:
        return None
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    return dict(row)
