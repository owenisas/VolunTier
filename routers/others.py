from fastapi import APIRouter, Depends, HTTPException, status
import sqlite3, math
from fastapi import APIRouter, Depends
from typing import List
from database import get_db
from routers.auth import get_current_user
from schemas import User, ConnectionXP

router = APIRouter()
