# routers/users.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from database import get_db
from schemas import UserCreate, User, RegisterResponse, LoginRequest, TokenResponse, UserEdit
from utils import create_access_token, create_verification_token, send_verification_email
import sqlite3
from datetime import timedelta
from .auth import get_current_user, hash_password, verify_password

router = APIRouter()



@router.get("/stats", response_model=dict)
def my_participation_stats(
    db: sqlite3.Connection = Depends(get_db),
    me: dict = Depends(get_current_user)
):
    """
    Return total events participated (registered) and total volunteer hours based on event durations.
    """
    cursor = db.cursor()
    # Count registered participations
    cursor.execute(
        "SELECT COUNT(*) AS total_events, COALESCE(SUM(e.duration), 0) AS total_minutes"
        " FROM Event_Users eu"
        " JOIN Events e ON eu.event_id = e.event_id"
        " WHERE eu.user_id = ? AND eu.volunteer_state = 'registered'",
        (me["user_id"],)
    )
    row = cursor.fetchone()
    total_events = row["total_events"]
    total_hours = row["total_minutes"] / 60
    return {"total_events": total_events, "total_hours": total_hours}


@router.put("/users/edit", response_model=User)
def edit_user(
    user_edit: UserEdit,
    current_user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()

    # If a new username is provided and it's different, ensure it's not already taken.
    if user_edit.username and user_edit.username != current_user["username"]:
        cursor.execute("SELECT * FROM Users WHERE username = ?", (user_edit.username,))
        if cursor.fetchone() is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    # Build the update query dynamically based on the provided fields.
    update_fields = []
    params = []

    if user_edit.username is not None:
        update_fields.append("username = ?")
        params.append(user_edit.username)
    if user_edit.profile is not None:
        update_fields.append("profile = ?")
        params.append(user_edit.profile)
    if user_edit.age is not None:
        update_fields.append("age = ?")
        params.append(user_edit.age)

    if not update_fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")

    query = f"UPDATE Users SET {', '.join(update_fields)} WHERE user_id = ?"
    params.append(current_user["user_id"])
    try:
        cursor.execute(query, tuple(params))
        db.commit()
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

    # Retrieve and return the updated user.
    cursor.execute("SELECT * FROM Users WHERE user_id = ?", (current_user["user_id"],))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")

    return User(**row)
@router.get("/users/me", response_model=User)
def me(current_user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Users WHERE user_id = ?", (current_user.get("user_id"),))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**row)
@router.post("/register", response_model=RegisterResponse)
def register(user: UserCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    # Check if email already exists.
    cursor.execute("SELECT * FROM Users WHERE email = ?", (user.email,))
    if cursor.fetchone() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    # Check if username already exists.
    cursor.execute("SELECT * FROM Users WHERE username = ?", (user.username,))
    if cursor.fetchone() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    cursor.execute(
        "INSERT INTO Users (username, email, hash_password, full_name, profile, pronouns, age) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user.username, user.email, hash_password(user.password), user.full_name, user.profile, user.pronouns, user.age)
    )
    db.commit()
    user_id = cursor.lastrowid
    cursor.execute("SELECT * FROM Users WHERE user_id = ?", (user_id,))
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
    cursor.execute("SELECT * FROM Users WHERE email = ?", (login_request.email,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    stored_hash = row["hash_password"]
    if not verify_password(login_request.password, stored_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    access_token = create_access_token(str(row["user_id"]))
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**row)
