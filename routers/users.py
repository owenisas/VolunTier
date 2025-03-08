# routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from database import get_db
from schemas import UserCreate, User, RegisterResponse, LoginRequest, TokenResponse
from utils import create_access_token, create_verification_token, send_verification_email
import sqlite3
from datetime import timedelta

router = APIRouter()


@router.post("/register", response_model=RegisterResponse)
def register(user: UserCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    # Check if email already exists.
    cursor.execute("SELECT * FROM User WHERE email = ?", (user.email,))
    if cursor.fetchone() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    # Check if username already exists.
    cursor.execute("SELECT * FROM User WHERE username = ?", (user.username,))
    if cursor.fetchone() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    cursor.execute(
        "INSERT INTO User (username, email, hash_password, full_name, profile, profile_pic, age) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user.username, user.email, user.hash_password, user.full_name, user.profile, user.profile_pic, user.age)
    )
    db.commit()
    user_id = cursor.lastrowid
    cursor.execute("SELECT * FROM User WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found after registration")

    user_obj = User(**row)
    # Create verification token and send email
    verification_token = create_verification_token(user_obj.user_id)
    send_verification_email(user_obj.email, verification_token)

    # Generate access token for immediate login
    access_token = create_access_token(str(user_obj.user_id))
    return RegisterResponse(user=user_obj, access_token=access_token, token_type="bearer")


@router.post("/login", response_model=TokenResponse)
def login(login_request: LoginRequest, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM User WHERE email = ?", (login_request.email,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    stored_password = row["hash_password"]
    if stored_password != login_request.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    access_token = create_access_token(str(row["user_id"]))
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM User WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**row)
