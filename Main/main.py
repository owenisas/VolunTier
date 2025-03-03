import sqlite3
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt

app = FastAPI()

# JWT configuration (replace SECRET_KEY with a secure key in production)
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DATABASE = "app_database.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # enables dict-like access to rows
    try:
        yield conn
    finally:
        conn.close()


# Use OAuth2 to extract the token from the Authorization header.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: sqlite3.Connection = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    cursor = db.cursor()
    cursor.execute("SELECT * FROM User WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)


# --------------------------
# Pydantic Models
# --------------------------

class UserCreate(BaseModel):
    username: str
    email: str
    hash_password: str
    full_name: str
    profile: str = None
    age: int = None


class User(BaseModel):
    user_id: int
    username: str
    email: str
    full_name: str
    profile: str = None
    age: int = None
    verification: int

    class Config:
        orm_mode = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# New response model for register that includes the user and token
class RegisterResponse(BaseModel):
    user: User
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    email: str
    password: str


class EventCreate(BaseModel):
    title: str
    details: str
    time: datetime  # User provided event start time
    picture: str = None
    event_link: str = None
    location: str = None
    certificate: int = 0
    requirements: str = None
    contact_methods: str = None
    instructions: str = None
    max_participants: int = None
    duration: int = None  # Duration in minutes
    status: bool = True  # True means upcoming/active


class Event(BaseModel):
    event_id: int
    time: datetime  # Returned as a datetime
    title: str
    details: str
    picture: str = None
    organizer: str = None
    organization_name: str = None
    event_link: str = None
    location: str = None
    certificate: int
    requirements: str = None
    contact_methods: str = None
    instructions: str = None
    max_participants: int = None
    duration: int = None
    status: bool  # True for upcoming/active, False for ended

    class Config:
        orm_mode = True


# --------------------------
# Endpoints
# --------------------------

@app.post("/register", response_model=RegisterResponse)
def register(user: UserCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    # Check if email already exists.
    cursor.execute("SELECT * FROM User WHERE email = ?", (user.email,))
    if cursor.fetchone() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    # Check if username already exists.
    cursor.execute("SELECT * FROM User WHERE username = ?", (user.username,))
    if cursor.fetchone() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    cursor.execute(
        "INSERT INTO User (username, email, hash_password, full_name, profile, age) VALUES (?, ?, ?, ?, ?, ?)",
        (user.username, user.email, user.hash_password, user.full_name, user.profile, user.age)
    )
    db.commit()
    user_id = cursor.lastrowid
    cursor.execute("SELECT * FROM User WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found after registration")

    user_obj = User(**row)
    # Generate JWT token for the newly registered user.
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {"sub": str(user_obj.user_id), "exp": expire}
    access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return RegisterResponse(user=user_obj, access_token=access_token, token_type="bearer")


@app.post("/login", response_model=TokenResponse)
def login(login_request: LoginRequest, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM User WHERE email = ?", (login_request.email,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    stored_password = row["hash_password"]
    if stored_password != login_request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {"sub": str(row["user_id"]), "exp": expire}
    access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return TokenResponse(access_token=access_token, token_type="bearer")


@app.post("/events/create", response_model=Event)
def create_event(
        event: EventCreate,
        current_user: dict = Depends(get_current_user),
        db: sqlite3.Connection = Depends(get_db)
):
    try:
        cursor = db.cursor()
        # Insert new event into the events table using the user-provided time.
        cursor.execute(
            """
            INSERT INTO events (
                time, title, details, picture, organizer, organization_name, event_link, location,
                certificate, requirements, contact_methods, instructions, max_participants, duration, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.time.isoformat(),  # Store the provided datetime as ISO string
                event.title,
                event.details,
                event.picture,
                current_user.get("full_name"),  # Use current user's full name as organizer.
                None,  # organization_name can be provided if needed.
                event.event_link,
                event.location,
                event.certificate,
                event.requirements,
                event.contact_methods,
                event.instructions,
                event.max_participants,
                event.duration,
                int(event.status)  # Convert boolean to int: True -> 1, False -> 0
            )
        )
        db.commit()
        event_id = cursor.lastrowid

        # Automatically assign current user the "organizer" role.
        cursor.execute(
            "INSERT INTO Event_Users (user_id, event_id, role) VALUES (?, ?, ?)",
            (current_user["user_id"], event_id, "organizer")
        )
        db.commit()

        # Retrieve the newly created event.
        cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Event not found after creation")
        return Event(**row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.post("/events/{event_id}/join", response_model=dict)
def join_event(event_id: int, current_user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    # Check if user already has a role for this event.
    cursor.execute("SELECT role FROM Event_Users WHERE event_id = ? AND user_id = ?",
                   (event_id, current_user["user_id"]))
    row = cursor.fetchone()
    if row:
        return {"message": f"You already joined this event with role: {row['role']}", "role": row['role']}
    default_role = "participant"
    cursor.execute("INSERT INTO Event_Users (user_id, event_id, role) VALUES (?, ?, ?)",
                   (current_user["user_id"], event_id, default_role))
    db.commit()
    return {"message": "You have successfully joined the event.", "role": default_role}


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM User WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**row)


@app.get("/events/{event_id}", response_model=Event)
def get_event(event_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return Event(**row)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
