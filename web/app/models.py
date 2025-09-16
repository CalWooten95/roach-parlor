from sqlalchemy import Column, Integer, String, ForeignKey, Text, Enum, DateTime, func
from sqlalchemy.orm import relationship
from .database import Base
import enum
import re


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
    legs = relationship("WagerLeg", back_populates="wager", cascade="all, delete-orphan")

    @property
    def payout(self):
        """Return the potential profit for the wager based on its line."""
        if self.amount is None:
            return None

        multiplier = self._odds_multiplier()
        if multiplier is None:
            return None

        return round(self.amount * multiplier, 2)

    def _odds_multiplier(self):
        """Derive a multiplier from American odds or decimal-style lines."""
        if not self.line:
            return None

        match = re.search(r"[-+]?\d+(?:\.\d+)?", str(self.line))
        if not match:
            return None

        value = float(match.group())
        if value == 0:
            return None

        # Treat large absolute values as American odds; otherwise assume decimal odds
        if abs(value) >= 10:
            if value > 0:
                return value / 100
            return 100 / abs(value)

        return value


class WagerLegStatus(str, enum.Enum):
    open = "open"
    won = "won"
    lost = "lost"


class WagerLeg(Base):
    __tablename__ = "wager_legs"

    id = Column(Integer, primary_key=True, index=True)
    wager_id = Column(Integer, ForeignKey("wagers.id", ondelete="CASCADE"))
    description = Column(Text)
    status = Column(Enum(WagerLegStatus), default=WagerLegStatus.open)

    wager = relationship("Wager", back_populates="legs")

