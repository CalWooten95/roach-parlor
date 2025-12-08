# Pydantic schemas
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List


class LeagueBase(BaseModel):
    key: str
    name: str
    display_name: Optional[str] = None
    sport: Optional[str] = None


class LeagueCreate(LeagueBase):
    pass


class League(LeagueBase):
    id: int

    class Config:
        orm_mode = True


class TeamBase(BaseModel):
    league_id: int
    external_id: Optional[str] = None
    location: Optional[str] = None
    name: str
    nickname: Optional[str] = None
    abbreviation: Optional[str] = None
    logo_url: Optional[str] = None


class TeamCreate(TeamBase):
    pass


class Team(TeamBase):
    id: int

    class Config:
        orm_mode = True


class PlayerBase(BaseModel):
    team_id: int
    external_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: str
    position: Optional[str] = None
    jersey_number: Optional[str] = None


class PlayerCreate(PlayerBase):
    pass


class Player(PlayerBase):
    id: int

    class Config:
        orm_mode = True


class TeamSummary(BaseModel):
    id: int
    league_id: int
    name: str
    location: Optional[str] = None
    display_name: Optional[str] = None
    nickname: Optional[str] = None
    abbreviation: Optional[str] = None
    logo_url: Optional[str] = None

    class Config:
        orm_mode = True


class PlayerSummary(BaseModel):
    id: int
    full_name: str
    position: Optional[str] = None
    jersey_number: Optional[str] = None

    class Config:
        orm_mode = True


class TeamWithPlayers(Team):
    players: List[PlayerSummary] = Field(default_factory=list)


class LeagueWithTeams(League):
    teams: List[TeamWithPlayers] = Field(default_factory=list)

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
    archived: Optional[bool] = False
    discord_message_id: Optional[str] = None
    discord_channel_id: Optional[str] = None
    archive_reacted: Optional[bool] = False
    legs: List[WagerLeg] = Field(default_factory=list)
    amount: Optional[float] = None
    line: Optional[str] = None
    is_free_play: Optional[bool] = False


class WagerMatchupCreate(BaseModel):
    league_id: Optional[int] = None
    home_team_id: Optional[int] = None
    away_team_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None


class WagerMatchup(BaseModel):
    id: int
    league: Optional[League] = None
    home_team: Optional[TeamSummary] = None
    away_team: Optional[TeamSummary] = None
    scheduled_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class WagerCreate(WagerBase):
    legs: List[WagerLegCreate] = Field(default_factory=list)
    matchup: Optional[WagerMatchupCreate] = None


class Wager(WagerBase):
    id: int
    user_id: int
    created_at: Optional[str]
    resulted_at: Optional[str] = None
    matchup: Optional[WagerMatchup] = None

    class Config:
        orm_mode = True
