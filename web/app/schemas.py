# Pydantic schemas
from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    discord_id: str
    display_name: str
    profile_pic_url: Optional[str]

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    class Config:
        orm_mode = True

class WagerBase(BaseModel):
    description: str
    image_url: Optional[str]
    status: Optional[str] = "open"

class WagerCreate(WagerBase):
    pass

class Wager(WagerBase):
    id: int
    user_id: int
    created_at: Optional[str]
    class Config:
        orm_mode = True
