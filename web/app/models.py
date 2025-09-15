from sqlalchemy import Column, Integer, String, ForeignKey, Text, Enum, DateTime, func
from sqlalchemy.orm import relationship
from .database import Base
import enum


class WagerStatus(str, enum.Enum):
    open = "open"
    won = "won"
    lost = "lost"
    removed = "removed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    discord_id = Column(String, unique=True, index=True)
    display_name = Column(String)
    profile_pic_url = Column(String)
    wagers = relationship("Wager", back_populates="user")


class Wager(Base):
    __tablename__ = "wagers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    description = Column(Text)
    amount = Column(Integer)            # <-- Add this
    line = Column(String)               # <-- And this
    image_url = Column(String, nullable=True)
    status = Column(Enum(WagerStatus), default=WagerStatus.open)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="wagers")

