# database.py
import sqlite3
from config import DATABASE

def get_db():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Access rows as dictionaries
    try:
        yield conn
    finally:
        conn.close()
