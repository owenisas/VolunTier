# routers/events.py
from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from schemas import EventCreate, Event, EventImage
import sqlite3
from routers.users import router as user_router  # if needed for dependency
import jwt
from config import SECRET_KEY, ALGORITHM
from datetime import datetime
from typing import List, Optional
from datetime import timedelta, timezone
from .auth import get_current_user, get_current_user_optional
from typing import Optional
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()


from schemas import Event, EventImage  # Ensure these are imported
from datetime import datetime


@router.get("/tier")
def your_tier(db: sqlite3.Connection = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Retrieves events that the current user has joined (from the Event_Users table)
    and returns a dictionary containing the current user's username, a list of events,
    the count of events (volCount), and the total hours computed from event durations.
    """
    cursor = db.cursor()
    # Get all event IDs that the current user has joined
    cursor.execute("SELECT event_id FROM Event_Users WHERE user_id = ?", (current_user["user_id"],))
    joined_rows = cursor.fetchall()

    if not joined_rows:
        events = []
    else:
        # Extract event_ids from the result
        event_ids = [row["event_id"] for row in joined_rows]
        # Build the IN clause dynamically
        placeholders = ','.join('?' for _ in event_ids)
        query = f"SELECT * FROM events WHERE event_id IN ({placeholders}) ORDER BY time ASC"
        cursor.execute(query, event_ids)
        rows = cursor.fetchall()

        events = []
        for row in rows:
            event = dict(row)
            event_id = event.get("event_id")
            # Retrieve the first image for this event, ordered by creation time
            cursor.execute(
                "SELECT image_id, image_url, created_at FROM Event_Images WHERE event_id = ? ORDER BY created_at ASC LIMIT 1",
                (event_id,)
            )
            image_row = cursor.fetchone()
            if image_row:
                event_image = EventImage(
                    image_id=image_row["image_id"],
                    event_id=event_id,
                    image_url=image_row["image_url"],
                    created_at=image_row["created_at"]
                )
                event["images"] = [event_image]
            else:
                event["images"] = []
            events.append(Event(**event))

    # Extract username from current_user (assuming it exists in the user table)
    username = current_user.get("username")
    # volCount is the number of events joined
    volCount = len(events)
    # Calculate total minutes from event durations (if duration is not None)
    total_minutes = sum(e.duration if e.duration else 0 for e in events)
    # Convert minutes to hours
    total_hours = total_minutes / 60

    return {
        "username": username,
        "events": events,
        "volCount": volCount,
        "totalHours": total_hours
    }


@router.get("/events/get", response_model=List[Event])
def get_events_sorted_by_time(db: sqlite3.Connection = Depends(get_db)):
    """
    Retrieves up to 10 events from the database sorted by time in ascending order,
    and attaches the first image (if available) as a list of EventImage.
    """
    cursor = db.cursor()
    cursor.execute("SELECT * FROM events WHERE status = 1 ORDER BY time ASC LIMIT 10")
    rows = cursor.fetchall()
    events = []
    for row in rows:
        event = dict(row)
        event_id = event.get("event_id")
        # Retrieve the first image for this event, ordered by creation time
        cursor.execute(
            "SELECT image_id, image_url, created_at FROM Event_Images WHERE event_id = ? ORDER BY created_at ASC LIMIT 1",
            (event_id,)
        )
        image_row = cursor.fetchone()
        if image_row:
            # Create an EventImage instance
            # If created_at is a string, you may need to convert it to datetime
            event_image = EventImage(
                image_id=image_row["image_id"],
                event_id=event_id,
                image_url=image_row["image_url"],
                created_at=image_row["created_at"]
            )
            event["images"] = [event_image]
        else:
            event["images"] = []
        events.append(Event(**event))
    return events




@router.get("/events/search", response_model=List[Event])
def search_events(
        title: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        db: sqlite3.Connection = Depends(get_db)
):
    """
    Search events by title and/or by a date range.
    - title: searches for events containing this substring in the title.
    - start: earliest event time (inclusive).
    - end: latest event time (inclusive).
    """
    query = "SELECT * FROM events WHERE 1=1"
    params = []

    if title:
        query += " AND title LIKE ?"
        params.append(f"%{title}%")

    if start:
        query += " AND datetime(time) >= datetime(?)"
        params.append(start.isoformat())

    if end:
        query += " AND datetime(time) <= datetime(?)"
        params.append(end.isoformat())

    cursor = db.cursor()
    try:
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return [Event(**row) for row in rows]


@router.post("/events/create", response_model=Event)
def create_event(event: EventCreate, current_user: dict = Depends(get_current_user),
                 db: sqlite3.Connection = Depends(get_db)):
    try:
        end_time = event.time + timedelta(minutes=event.duration)

        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO events (
                time, end_time, title, details, organizer, organization_name, event_link, location,
                certificate, requirements, contact_methods, instructions, max_participants, duration, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.time.isoformat(),
                end_time.isoformat(),
                event.title,
                event.details,
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
def join_event(
        event_id: int,
        current_user: dict = Depends(get_current_user),
        db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    # Check if user already has a role in this event.
    cursor.execute(
        "SELECT role FROM Event_Users WHERE event_id = ? AND user_id = ?",
        (event_id, current_user["user_id"])
    )
    row = cursor.fetchone()
    if row:
        return {
            "message": f"You already joined this event with role: {row['role']}",
            "role": row["role"]
        }

    # Retrieve event details to check max_participants.
    cursor.execute(
        "SELECT max_participants FROM events WHERE event_id = ?",
        (event_id,)
    )
    event_row = cursor.fetchone()
    if event_row is None:
        raise HTTPException(status_code=404, detail="Event not found")

    max_participants = event_row["max_participants"]
    if max_participants is not None:
        # Count current participants in the event.
        cursor.execute(
            "SELECT COUNT(*) as count FROM Event_Users WHERE event_id = ?",
            (event_id,)
        )
        count_row = cursor.fetchone()
        current_count = count_row["count"] if count_row else 0
        if current_count >= max_participants:
            raise HTTPException(
                status_code=400,
                detail="Event is full, cannot join."
            )

    # If event is not full, add the user as a participant.
    cursor.execute(
        "INSERT INTO Event_Users (user_id, event_id, role) VALUES (?, ?)",
        (current_user["user_id"], event_id)
    )
    db.commit()
    return {"message": "You have successfully joined the event.", "role": "participant"}


@router.get("/events/{event_id}", response_model=Event)
def get_event(
    event_id: int,
    db: sqlite3.Connection = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    cursor = db.cursor()

    cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
    event_row = cursor.fetchone()

    if not event_row:
        raise HTTPException(status_code=404, detail="Event not found")

    event_data = dict(event_row)

    # Fetch associated images
    cursor.execute("SELECT * FROM Event_Images WHERE event_id = ?", (event_id,))
    image_rows = cursor.fetchall()

    if image_rows:
        event_images = [EventImage(**dict(row)) for row in image_rows]
    else:
        event_images = None  # Return None if no images

    event_data["images"] = event_images

    # Existing logic for contact_methods and status update
    event_end_time = datetime.fromisoformat(event_data["end_time"])
    now = now = datetime.now(timezone.utc)
    if now > event_end_time and event_data["status"] == 1:
        cursor.execute("UPDATE events SET status = 0 WHERE event_id = ?", (event_id,))
        db.commit()
        event_data["status"] = 0

    # Privacy handling
    if not current_user:
        event_data.pop("contact_methods", None)
    else:
        cursor.execute(
            "SELECT role FROM Event_Users WHERE event_id = ? AND user_id = ?",
            (event_id, current_user["user_id"])
        )
        role_row = cursor.fetchone()
        if not role_row or role_row["role"] != "organizer":
            event_data.pop("contact_methods", None)

    return Event(**event_data)


@router.put("/events/{event_id}/edit", response_model=Event)
def edit_event(
        event_id: int,
        updated_event: EventCreate,
        current_user: dict = Depends(get_current_user),
        db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    # Verify that the current user is the organizer for the event.
    cursor.execute(
        "SELECT role FROM Event_Users WHERE event_id = ? AND user_id = ?",
        (event_id, current_user["user_id"])
    )
    role_row = cursor.fetchone()
    if not role_row or role_row["role"] != "organizer":
        raise HTTPException(status_code=403, detail="Only the organizer can edit this event.")
    end_time = updated_event.time + timedelta(minutes=updated_event.duration)
    # Update the event with the new information, has to input unchanged information
    cursor.execute(
        """
        UPDATE events
        SET time = ?,
            end_time = ?,
            title = ?,
            details = ?,
            event_pic = ?,
            event_link = ?,
            location = ?,
            certificate = ?,
            requirements = ?,
            contact_methods = ?,
            instructions = ?,
            max_participants = ?,
            duration = ?,
            status = ?
        WHERE event_id = ?
        """,
        (
            updated_event.time.isoformat(),
            end_time.isoformat(),
            updated_event.title,
            updated_event.details,
            updated_event.event_pic,
            updated_event.event_link,
            updated_event.location,
            updated_event.certificate,
            updated_event.requirements,
            updated_event.contact_methods,
            updated_event.instructions,
            updated_event.max_participants,
            updated_event.duration,
            int(updated_event.status),
            event_id
        )
    )
    db.commit()

    # Retrieve and return the updated event.
    cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
    updated_row = cursor.fetchone()
    if updated_row is None:
        raise HTTPException(status_code=404, detail="Event not found after update")
    return Event(**updated_row)
