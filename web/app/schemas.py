# Pydantic schemas
from pydantic import BaseModel, Field
from typing import Optional, List

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

class WagerLegBase(BaseModel):
    description: str
    status: Optional[str] = "open"


class WagerLegCreate(WagerLegBase):
    pass


class WagerLeg(WagerLegBase):
    id: int

    class Config:
        orm_mode = True


class WagerBase(BaseModel):
    description: str
    image_url: Optional[str]
    status: Optional[str] = "open"
    legs: List[WagerLeg] = Field(default_factory=list)


class WagerCreate(WagerBase):
    legs: List[WagerLegCreate] = Field(default_factory=list)


class Wager(WagerBase):
    id: int
    user_id: int
    created_at: Optional[str]

    class Config:
        orm_mode = True
