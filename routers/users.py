# routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from database import get_db
from schemas import UserCreate, User, RegisterResponse, LoginRequest, TokenResponse, UserEdit
from utils import create_access_token, create_verification_token, send_verification_email
import sqlite3
from datetime import timedelta
from .auth import get_current_user

router = APIRouter()


@router.put("/users/edit", response_model=User)
def edit_user(
    user_edit: UserEdit,
    current_user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()

    # If a new username is provided and it's different, ensure it's not already taken.
    if user_edit.username and user_edit.username != current_user["username"]:
        cursor.execute("SELECT * FROM User WHERE username = ?", (user_edit.username,))
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

    query = f"UPDATE User SET {', '.join(update_fields)} WHERE user_id = ?"
    params.append(current_user["user_id"])
    try:
        cursor.execute(query, tuple(params))
        db.commit()
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

    # Retrieve and return the updated user.
    cursor.execute("SELECT * FROM User WHERE user_id = ?", (current_user["user_id"],))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")

    return User(**row)

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
