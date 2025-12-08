from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, models, database
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter(prefix="/wagers", tags=["wagers"])

class WagerLegPayload(BaseModel):
    description: str
    status: str | None = "open"


class WagerLegOut(BaseModel):
    id: int
    description: str
    status: str

    class Config:
        orm_mode = True


class TeamSummary(BaseModel):
    id: int
    league_id: int
    name: str
    location: str | None = None
    display_name: str | None = None
    nickname: str | None = None
    abbreviation: str | None = None
    logo_url: str | None = None

    class Config:
        orm_mode = True


class LeagueSummary(BaseModel):
    id: int
    key: str
    name: str
    display_name: str | None = None
    sport: str | None = None

    class Config:
        orm_mode = True


class WagerMatchupPayload(BaseModel):
    league_id: int | None = None
    home_team_id: int | None = None
    away_team_id: int | None = None
    scheduled_at: datetime | None = None


class WagerMatchupOut(BaseModel):
    id: int
    league: LeagueSummary | None = None
    home_team: TeamSummary | None = None
    away_team: TeamSummary | None = None
    scheduled_at: datetime | None = None

    class Config:
        orm_mode = True


class WagerCreate(BaseModel):
    user_id: int
    description: str
    amount: float
    line: str
    is_free_play: bool = False
    legs: list[WagerLegPayload] | None = None
    matchup: WagerMatchupPayload | None = None
    archived: bool | None = False
    discord_message_id: str | None = None
    discord_channel_id: str | None = None


class WagerOut(BaseModel):
    id: int
    user_id: int
    description: str
    amount: float
    line: str
    status: str
    archived: bool
    archive_reacted: bool
    is_free_play: bool
    resulted_at: datetime | None = None
    discord_message_id: str | None = None
    discord_channel_id: str | None = None
    payout: float | None = None
    legs: list[WagerLegOut] = Field(default_factory=list)
    matchup: WagerMatchupOut | None = None

    class Config:
        orm_mode = True


class ArchiveReactionTarget(BaseModel):
    id: int
    status: str
    archived: bool
    archive_reacted: bool
    discord_message_id: str | None = None
    discord_channel_id: str | None = None

    class Config:
        orm_mode = True


class ArchiveReactionUpdate(BaseModel):
    reacted: bool = True


@router.post("/", response_model=WagerOut)
def create_wager(wager: WagerCreate, db: Session = Depends(database.get_db)):
    user = crud.get_user(db, wager.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    legs = [leg.model_dump() for leg in (wager.legs or [])]
    matchup = wager.matchup.model_dump() if wager.matchup else None
    return crud.create_wager(
        db,
        user_id=wager.user_id,
        description=wager.description,
        amount=wager.amount,
        line=wager.line,
        is_free_play=wager.is_free_play,
        legs=legs,
        matchup=matchup,
        archived=bool(wager.archived),
        discord_message_id=wager.discord_message_id,
        discord_channel_id=wager.discord_channel_id,
    )


@router.get("/{user_id}", response_model=list[WagerOut])
def list_user_wagers(user_id: int, db: Session = Depends(database.get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.get_user_wagers(db, user_id)


@router.patch("/{wager_id}/status", response_model=WagerOut)
def update_status(wager_id: int, status: str, db: Session = Depends(database.get_db)):
    wager = crud.update_wager_status(db, wager_id, status)
    if not wager:
        raise HTTPException(status_code=404, detail="Wager not found")
    return wager


@router.patch("/{wager_id}/archive", response_model=WagerOut)
def update_archive_state(wager_id: int, archived: bool, db: Session = Depends(database.get_db)):
    wager = crud.set_wager_archived(db, wager_id, archived)
    if not wager:
        raise HTTPException(status_code=404, detail="Wager not found")
    return wager


@router.get("/archive/pending", response_model=list[ArchiveReactionTarget])
def list_archive_reactions(limit: int = 50, db: Session = Depends(database.get_db)):
    return crud.get_archived_wagers_pending_reaction(db, limit=limit)


@router.post("/{wager_id}/archive/reacted", response_model=ArchiveReactionTarget)
def mark_archive_reaction(wager_id: int, update: ArchiveReactionUpdate, db: Session = Depends(database.get_db)):
    wager = crud.mark_wager_archive_reacted(db, wager_id, update.reacted)
    if not wager:
        raise HTTPException(status_code=404, detail="Wager not found")
    return wager


@router.delete("/{wager_id}", response_model=WagerOut)
def delete_wager(wager_id: int, db: Session = Depends(database.get_db)):
    wager = crud.delete_wager(db, wager_id)
    if not wager:
        raise HTTPException(status_code=404, detail="Wager not found")
    return wager


@router.patch("/legs/{leg_id}/status", response_model=WagerLegOut)
def update_leg_status(leg_id: int, status: str, db: Session = Depends(database.get_db)):
    leg = crud.update_wager_leg_status(db, leg_id, status)
    if not leg:
        raise HTTPException(status_code=404, detail="Wager leg not found")
    return leg
