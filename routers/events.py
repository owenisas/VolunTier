# routers/events.py
from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from schemas import EventCreate, Event
import sqlite3
from routers.users import router as user_router  # if needed for dependency
from fastapi.security import OAuth2PasswordBearer
import jwt
from config import SECRET_KEY, ALGORITHM
from utils import create_access_token
from datetime import datetime

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: sqlite3.Connection = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM User WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)

@router.post("/events/create", response_model=Event)
def create_event(event: EventCreate, current_user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO events (
                time, title, details, event_pic, organizer, organization_name, event_link, location,
                certificate, requirements, contact_methods, instructions, max_participants, duration, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.time.isoformat(),
                event.title,
                event.details,
                event.event_pic,
                current_user.get("full_name"),
                None,
                event.event_link,
                event.location,
                event.certificate,
                event.requirements,
                event.contact_methods,
                event.instructions,
                event.max_participants,
                event.duration,
                int(event.status)
            )
        )
        db.commit()
        event_id = cursor.lastrowid

        # Automatically assign the current user the "organizer" role in Event_Users table
        cursor.execute(
            "INSERT INTO Event_Users (user_id, event_id, role) VALUES (?, ?, ?)",
            (current_user["user_id"], event_id, "organizer")
        )
        db.commit()

        cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Event not found after creation")
        return Event(**row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.post("/events/{event_id}/join", response_model=dict)
def join_event(event_id: int, current_user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT role FROM Event_Users WHERE event_id = ? AND user_id = ?", (event_id, current_user["user_id"]))
    row = cursor.fetchone()
    if row:
        return {"message": f"You already joined this event with role: {row['role']}", "role": row["role"]}
    default_role = "participant"
    cursor.execute("INSERT INTO Event_Users (user_id, event_id, role) VALUES (?, ?, ?)", (current_user["user_id"], event_id, default_role))
    db.commit()
    return {"message": "You have successfully joined the event.", "role": default_role}

@router.get("/events/{event_id}", response_model=Event)
def get_event(event_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return Event(**row)
