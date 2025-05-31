# routers/screenshots.py

import os
import re
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import aiofiles

router = APIRouter(
    prefix="/screenshots",
    tags=["screenshots"]
)

# Directory to store uploaded screenshots
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Ensure it exists :contentReference[oaicite:10]{index=10}

def get_next_index(upload_dir: str) -> int:
    """
    Scan all files in upload_dir matching 'screenshot_{number}.png'
    and return the next index (max + 1). If none exist, return 1.
    """
    pattern = re.compile(r"^screenshot_(\d+)\.png$")
    max_idx = 0

    # List all files in the directory
    for fname in os.listdir(upload_dir):  # :contentReference[oaicite:11]{index=11}
        match = pattern.match(fname)
        if match:
            idx = int(match.group(1))
            if idx > max_idx:
                max_idx = idx

    return max_idx + 1  # Next available index


@router.post("/upload/")
async def upload_screenshot(file: UploadFile = File(...)):
    """
    Receives a multipart/form-data 'file', renames it to 'screenshot_{n}.png'
    (where n is the next available index), saves it asynchronously, and
    returns the new filename and URL.
    """
    # 1. Validate that the client sent a PNG (or adjust to allow JPEG)
    if file.content_type != "image/png":
        # If you want to allow JPEG as well:
        # if file.content_type not in ("image/png", "image/jpeg"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PNG is supported.")  # :contentReference[oaicite:12]{index=12}

    # 2. Compute the next index for naming
    try:
        next_idx = get_next_index(UPLOAD_DIR)
    except Exception as e:
        # In case directory read fails
        raise HTTPException(status_code=500, detail=f"Error scanning upload directory: {e}")  # :contentReference[oaicite:13]{index=13}

    # 3. Construct the new filename (PNG)
    new_filename = f"screenshot_{next_idx}.png"
    save_path = os.path.join(UPLOAD_DIR, new_filename)

    # 4. Asynchronously write to disk (read entire file into memory; OK for small files)
    try:
        async with aiofiles.open(save_path, "wb") as out_file:
            content = await file.read()       # Read all bytes from UploadFile :contentReference[oaicite:14]{index=14}
            await out_file.write(content)     # Async write to file :contentReference[oaicite:15]{index=15}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")  # :contentReference[oaicite:16]{index=16}

    # 5. Return JSON with the new filename and its public URL path
    return {
        "filename": new_filename,
        "url": f"/screenshots/{new_filename}"
    }


@router.get("/{filename}")
async def get_screenshot(filename: str):
    """
    Streams the requested screenshot back to the client.
    If not found, returns a 404 error.
    """
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):   # :contentReference[oaicite:17]{index=17}
        raise HTTPException(status_code=404, detail="File not found")

    # Use FileResponse to serve the image
    # If you later want to serve JPEGs too, detect extension and set media_type accordingly
    return FileResponse(
        path=file_path,
        media_type="image/png",
        filename=filename
    )  # :contentReference[oaicite:18]{index=18}
