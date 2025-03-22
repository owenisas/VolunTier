from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query
from fastapi.responses import FileResponse
import os, uuid
from database import get_db
import sqlite3

# Import get_current_user from a common location (here, from routers.events for example)
from routers.events import get_current_user

router = APIRouter()


# Endpoint to serve an image from a given path.
@router.get("/images/{folder}/{image_name}")
def get_image(folder: str, image_name: str):
    # Only allow "profile" and "event" folders for security.
    if folder not in ["profile", "event"]:
        raise HTTPException(status_code=400, detail="Invalid folder")
    file_path = os.path.join("images", folder, image_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)


@router.post("/images/upload", response_model=dict)
async def upload_image(
        file: UploadFile = File(...),
        type: str = Query(..., regex="^(profile|event)$"),
        event_id: int = None,
        current_user: dict = Depends(get_current_user),
        db: sqlite3.Connection = Depends(get_db)
):
    """
    Upload an image and update the database:
     - For type 'profile': updates the current user's profile_pic.
     - For type 'event': requires event_id and updates the event_pic for that event
       (only if the current user is the organizer).
    """
    # Validate file extension.
    allowed_extensions = {"jpg", "jpeg", "png", "gif"}
    filename_parts = file.filename.split(".")
    if len(filename_parts) < 2 or filename_parts[-1].lower() not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    # Determine subfolder based on type.
    folder = os.path.join("images", type)
    os.makedirs(folder, exist_ok=True)

    # Generate a unique filename.
    file_ext = filename_parts[-1].lower()
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(folder, unique_filename)

    # Save the file locally.
    try:
        with open(file_path, "wb") as f:
            contents = await file.read()
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    # Construct a URL for accessing the image (assuming your app serves it via /images route).
    image_url = f"/images/{type}/{unique_filename}"

    # Update the database record based on type.
    cursor = db.cursor()
    if type == "profile":
        # Update the current user's profile_pic field.
        cursor.execute(
            "UPDATE User SET profile_pic = ? WHERE user_id = ?",
            (image_url, current_user["user_id"])
        )
    elif type == "event":
        # Ensure event_id is provided.
        if event_id is None:
            raise HTTPException(status_code=400, detail="event_id is required for event images.")
        # Check if the current user is the organizer for the event.
        cursor.execute(
            "SELECT role FROM Event_Users WHERE event_id = ? AND user_id = ?",
            (event_id, current_user["user_id"])
        )
        role_row = cursor.fetchone()
        if not role_row or role_row["role"] != "organizer":
            raise HTTPException(status_code=403, detail="Only the organizer can update event photos.")
        # Update the event's event_pic field.
        cursor.execute(
            "UPDATE events SET event_pic = ? WHERE event_id = ?",
            (image_url, event_id)
        )
    db.commit()

    return {"file_path": file_path, "url": image_url}
