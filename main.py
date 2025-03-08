# main.py
from fastapi import FastAPI
from routers import users, events, verification, images
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import sqlite3
from config import DATABASE

app = FastAPI()

# Include routers
app.include_router(users.router)
app.include_router(events.router)
app.include_router(verification.router)
app.include_router(images.router)

# Background task: update event statuses based on time/duration
def update_event_statuses():
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE events
                SET status = 0
                WHERE datetime(time, '+' || duration || ' minutes') < datetime('now')
                  AND status = 1;
                """
            )
            conn.commit()
            print(f"Updated event statuses at {datetime.utcnow()}")
    except Exception as e:
        print("Error updating event statuses:", e)

@app.on_event("startup")
async def startup_event():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_event_statuses, 'interval', minutes=1)
    scheduler.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
