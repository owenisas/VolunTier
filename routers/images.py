from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query
from fastapi.responses import FileResponse
import os, uuid
from database import get_db
import sqlite3
from utils import create_image_url, decode_image_token
from datetime import datetime
from schemas import EventImage
# Import get_current_user from a common location (here, from routers.events for example)
from .auth import get_current_user
from typing import Optional, List

router = APIRouter()


# Endpoint to serve an image from a given path.
@router.get("/images/{filename}")
def get_image(filename: str):
    try:
        # Check if the file exists in either event or profile folders
        event_path = os.path.join("images", "event", filename)
        profile_path = os.path.join("images", "profile", filename)
        
        if os.path.exists(event_path):
            return FileResponse(event_path)
        elif os.path.exists(profile_path):
            return FileResponse(profile_path)
        else:
            raise HTTPException(status_code=404, detail="Image not found")

    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/events/{event_id}/images/upload", response_model=List[EventImage])
async def upload_event_images(
        event_id: int,
        files: List[UploadFile] = File(...),
        current_user: dict = Depends(get_current_user),
        db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()

    # Verify the current user is the organizer
    cursor.execute("SELECT role FROM Event_Users WHERE event_id = ? AND user_id = ?",
                   (event_id, current_user["user_id"]))
    role_row = cursor.fetchone()
    if not role_row or role_row["role"] != "organizer":
        raise HTTPException(status_code=403, detail="Only organizers can upload images.")

    allowed_extensions = {"jpg", "jpeg", "png", "gif"}
    folder = os.path.join("images", "event")
    os.makedirs(folder, exist_ok=True)

    uploaded_images = []
    for file in files:
        filename_parts = file.filename.split(".")
        if len(filename_parts) < 2 or filename_parts[-1].lower() not in allowed_extensions:
            continue  # Skip unsupported files

        file_ext = filename_parts[-1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(folder, unique_filename)

        with open(file_path, "wb") as f:
            contents = await file.read()
            f.write(contents)

        # Generate secure URL
        image_url = "http://app.volun-tier.com/images/" + unique_filename

        # Store in database
        cursor.execute(
            "INSERT INTO Event_Images (event_id, image_url) VALUES (?, ?)",
            (event_id, image_url)
        )
        image_id = cursor.lastrowid
        db.commit()

        uploaded_images.append(EventImage(
            image_id=image_id,
            event_id=event_id,
            image_url=image_url,
            created_at=datetime.utcnow()
        ))

    return uploaded_images


@router.post("/users/profile/image/upload", response_model=dict)
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    allowed_extensions = {"jpg", "jpeg", "png", "gif"}
    ext = file.filename.split(".")[-1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    folder = os.path.join("images", "profile")
    os.makedirs(folder, exist_ok=True)

    unique_filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(folder, unique_filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    image_url = "http://app.volun-tier.com/images/" + unique_filename

    cursor = db.cursor()
    cursor.execute(
        "UPDATE Users SET profile_pic_url = ? WHERE user_id = ?",
        (image_url, current_user["user_id"])
    )
    db.commit()

    return {"secure_url": image_url}

