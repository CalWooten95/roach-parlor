from sqlalchemy import Column, Integer, String, ForeignKey, Text, Enum, DateTime, func
from sqlalchemy.orm import relationship
from .database import Base
import enum
import re


class League(Base):
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    name = Column(String, unique=True)
    display_name = Column(String, nullable=True)
    sport = Column(String, nullable=True)

    teams = relationship(
        "Team",
        back_populates="league",
        cascade="all, delete-orphan",
    )


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id", ondelete="CASCADE"), nullable=False)
    external_id = Column(String, nullable=True, index=True)
    location = Column(String, nullable=True)
    name = Column(String, nullable=False)
    nickname = Column(String, nullable=True)
    abbreviation = Column(String, nullable=True, index=True)
    logo_url = Column(String, nullable=True)

    league = relationship("League", back_populates="teams")
    players = relationship(
        "Player",
        back_populates="team",
        cascade="all, delete-orphan",
    )
    home_matchups = relationship(
        "WagerMatchup",
        back_populates="home_team",
        foreign_keys="WagerMatchup.home_team_id",
    )
    away_matchups = relationship(
        "WagerMatchup",
        back_populates="away_team",
        foreign_keys="WagerMatchup.away_team_id",
    )

    @property
    def display_name(self):
        location = (self.location or "").strip()
        nickname = (self.nickname or "").strip()
        name = (self.name or "").strip()

        parts: list[str] = []
        if location:
            parts.append(location)

        preferred = nickname or name
        if preferred:
            if not parts or preferred.lower() != parts[-1].lower():
                parts.append(preferred)

        if not parts:
            return ""

        # Remove duplicate consecutive tokens (e.g., "New York New York")
        cleaned: list[str] = []
        for part in parts:
            if not cleaned or cleaned[-1].lower() != part.lower():
                cleaned.append(part)

        return " ".join(cleaned)


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    external_id = Column(String, nullable=True, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    full_name = Column(String, nullable=False)
    position = Column(String, nullable=True)
    jersey_number = Column(String, nullable=True)

    team = relationship("Team", back_populates="players")


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
    matchup = relationship(
        "WagerMatchup",
        back_populates="wager",
        cascade="all, delete-orphan",
        uselist=False,
    )

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


class WagerMatchup(Base):
    __tablename__ = "wager_matchups"

    id = Column(Integer, primary_key=True, index=True)
    wager_id = Column(Integer, ForeignKey("wagers.id", ondelete="CASCADE"), unique=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=True)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)

    wager = relationship("Wager", back_populates="matchup")
    league = relationship("League")
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matchups")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matchups")

