# main.py
from fastapi import FastAPI
from routers import users, events, verification, images
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import sqlite3
from config import DATABASE
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         # Allow any origin
    allow_credentials=True,      # Note: if you allow credentials, using "*" is not recommended
    allow_methods=["*"],         # Allow all HTTP methods
    allow_headers=["*"],         # Allow all headers
)

# Include routers
app.include_router(users.router)
app.include_router(events.router)
app.include_router(verification.router)
app.include_router(images.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
