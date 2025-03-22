# schemas.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

# User models
class UserCreate(BaseModel):
    username: Optional[str] = None
    email: str
    hash_password: str
    full_name: Optional[str] = None
    profile: Optional[str] = None
    profile_pic: Optional[str] = None  # URL or file path
    age: Optional[int] = None

class UserEdit(BaseModel):
    username: Optional[str] = None
    profile: Optional[str] = None
    age: Optional[int] = None
    
class User(BaseModel):
    user_id: int
    username: str
    email: str
    full_name: str
    profile: Optional[str] = None
    profile_pic: Optional[str] = None
    age: Optional[int] = None
    verification: int

    class Config:
        orm_mode = True

# Token models
class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class RegisterResponse(BaseModel):
    user: User
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    email: str
    password: str

# Event models
class EventCreate(BaseModel):
    title: str
    details: str
    time: datetime  # User provided event start time
    event_pic: Optional[str] = None  # URL or file path for event picture
    event_link: Optional[str] = None
    location: Optional[str] = None
    certificate: int = 0
    requirements: Optional[str] = None
    contact_methods: Optional[str] = None
    instructions: Optional[str] = None
    max_participants: Optional[int] = None
    duration: Optional[int] = None  # Duration in minutes
    status: bool = True  # True means upcoming/active

class Event(BaseModel):
    event_id: int
    time: datetime
    title: str
    details: str
    event_pic: Optional[str] = None
    organizer: Optional[str] = None
    organization_name: Optional[str] = None
    event_link: Optional[str] = None
    location: Optional[str] = None
    certificate: int
    requirements: Optional[str] = None
    contact_methods: Optional[str] = None
    instructions: Optional[str] = None
    max_participants: Optional[int] = None
    duration: Optional[int] = None
    status: bool  # True for upcoming/active, False for ended

    class Config:
        orm_mode = True
