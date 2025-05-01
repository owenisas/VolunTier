# routers/xp.py
from fastapi import APIRouter, Depends, HTTPException, status
import sqlite3, math
from fastapi import APIRouter, Depends
from typing import List
from database import get_db
from routers.auth import get_current_user
from schemas import User, ConnectionXP

router = APIRouter()
def xp_to_level(xp: int):
    """
    Maps a user's total XP to a rank with metadata based on predefined tiers.
    Returns a dict with:
      - rank: str
      - color: str
      - xp_range: str
      - vibe: str
    """
    tiers = [
        {"min_xp": 2000, "rank": "S-Rank",   "color": "Shiny Purple",  "xp_range": "2000+ XP",      "vibe": "🏅 Top 1% of the platform"},
        {"min_xp": 1500, "rank": "Ruby",     "color": "Red-Pink",      "xp_range": "1500–1999 XP",   "vibe": "Power user / Leader"},
        {"min_xp": 1000, "rank": "Diamond",  "color": "Deep Blue",     "xp_range": "1000–1499 XP",   "vibe": "Community role model"},
        {"min_xp": 600,  "rank": "Platinum", "color": "Light Blue",    "xp_range": "600–999 XP",     "vibe": "Skilled / Trusted volunteer"},
        {"min_xp": 300,  "rank": "Gold",     "color": "Gold-Yellow",   "xp_range": "300–599 XP",     "vibe": "Committed contributor"},
        {"min_xp": 100,  "rank": "Silver",   "color": "Silver-White",  "xp_range": "100–299 XP",     "vibe": "Actively volunteering"},
        {"min_xp": 1,    "rank": "Bronze",   "color": "Brown-Copper",  "xp_range": "1–99 XP",        "vibe": "Casual start"},
        {"min_xp": 0,    "rank": "No Rank",  "color": "Grey",          "xp_range": "0 XP",           "vibe": "Newbie / Just joined"},
    ]
    # Find highest tier for which xp >= min_xp
    for tier in tiers:
        if xp >= tier["min_xp"]:
            return tier
    # Fallback (should not happen)
    return tiers[-1]

@router.get("/connections", response_model=List[User])
def list_connections(db: sqlite3.Connection = Depends(get_db), me=Depends(get_current_user)):
    cursor = db.cursor()
    cursor.execute("""
      SELECT u.* 
        FROM User_Connections c
        JOIN Users u ON
          (u.user_id = c.user_a AND c.user_b = ?)
          OR (u.user_id = c.user_b AND c.user_a = ?)
      """,
                   (me["user_id"], me["user_id"]))
    return [User(**row) for row in cursor.fetchall()]


@router.post("/connections/{other_id}", status_code=status.HTTP_201_CREATED)
def add_connection(other_id: int, db: sqlite3.Connection = Depends(get_db), me=Depends(get_current_user)):
    if other_id == me["user_id"]:
        raise HTTPException(400, "Cannot connect to yourself")
    a, b = sorted((me["user_id"], other_id))
    cursor = db.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO User_Connections(user_a, user_b) VALUES (?, ?)",
        (a, b)
    )
    db.commit()
    return {"message": "Connected successfully."}


@router.delete("/connections/{other_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_connection(other_id: int, db: sqlite3.Connection = Depends(get_db), me=Depends(get_current_user)):
    a, b = sorted((me["user_id"], other_id))
    cursor = db.cursor()
    cursor.execute("DELETE FROM User_Connections WHERE user_a = ? AND user_b = ?", (a, b))
    db.commit()


@router.get("/connections/ranking", response_model=List[ConnectionXP])
def rank_connections(
        db: sqlite3.Connection = Depends(get_db),
        me: dict = Depends(get_current_user)
):
    cursor = db.cursor()
    # 1. fetch all your connection IDs
    cursor.execute(
        """
        SELECT CASE
                 WHEN uc.user_a = ? THEN uc.user_b
                 ELSE uc.user_a
               END AS conn_id
          FROM User_Connections uc
         WHERE uc.user_a = ? OR uc.user_b = ?
        """,
        (me["user_id"], me["user_id"], me["user_id"])
    )
    rows = cursor.fetchall()
    conn_ids = [r["conn_id"] for r in rows]
    if not conn_ids:
        return []

    # 2. sum XP per connection and sort
    placeholders = ",".join("?" for _ in conn_ids)
    cursor.execute(
        f"""
        SELECT u.user_id,
               u.username,
               COALESCE(SUM(x.amount), 0) AS total_xp
          FROM Users u
          LEFT JOIN User_XP x ON x.user_id = u.user_id
         WHERE u.user_id IN ({placeholders})
         GROUP BY u.user_id
         ORDER BY total_xp DESC
        """,
        conn_ids
    )

    result = []
    for row in cursor.fetchall():
        xp = row["total_xp"]
        result.append(ConnectionXP(
            user_id=row["user_id"],
            username=row["username"],
            total_xp=xp,
            level=xp_to_level(xp)
        ))
    return result
