# schemas.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# User models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    profile: Optional[str] = None
    age: Optional[int] = None
    pronouns: Optional[str] = None


class User(BaseModel):
    user_id: int
    username: str
    email: str
    full_name: Optional[str] = None
    profile: Optional[str] = None
    profile_pic_url: Optional[str] = None
    age: Optional[int] = None,
    verified_email: Optional[str] = None
    edu_verification_email: Optional[str] = None
    work_verification_email: Optional[str] = None
    pronouns: Optional[str] = None

    class Config:
        orm_mode = True


class UserEdit(BaseModel):
    username: Optional[str] = None
    profile: Optional[str] = None
    age: Optional[int] = None


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


class EventImage(BaseModel):
    image_id: int
    event_id: int
    image_url: str
    created_at: datetime

    class Config:
        orm_mode = True


# Event models
class EventCreate(BaseModel):
    title: str
    details: str
    time: datetime
    duration: Optional[int] = None
    is_draft: bool = True  # new
    # you don’t need end_time here—server computes it
    event_link: Optional[str] = None
    location: Optional[str] = None
    certificate: int = 0
    requirements: Optional[str] = None
    contact_methods: Optional[str] = None
    instructions: Optional[str] = None
    max_participants: Optional[int] = None


class Event(BaseModel):
    event_id: int
    time: datetime
    end_time: datetime  # new
    is_draft: bool  # new
    title: str
    details: str
    images: List[EventImage] = []
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
    status: bool  # cast int→bool in your code

    class Config:
        orm_mode = True


class XPEntryCreate(BaseModel):
    amount: int
    reason: Optional[str] = None


class ConnectionXP(BaseModel):
    user_id: int
    username: str
    total_xp: int
    level: int

    class Config:
        orm_mode = True


class XPEntry(BaseModel):
    xp_id: int
    user_id: int
    amount: int
    reason: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class Connection(BaseModel):
    user_id: int
    connected_at: datetime

    class Config:
        orm_mode = True


class Skill(BaseModel):
    skill_category: int


class Tag(BaseModel):
    category: int


class SocialLink(BaseModel):
    link: str
