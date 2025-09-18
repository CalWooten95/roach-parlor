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
    legs: list[WagerLegPayload] | None = None
    matchup: WagerMatchupPayload | None = None


class WagerOut(BaseModel):
    id: int
    user_id: int
    description: str
    amount: float
    line: str
    status: str
    payout: float | None = None
    legs: list[WagerLegOut] = Field(default_factory=list)
    matchup: WagerMatchupOut | None = None

    class Config:
        orm_mode = True


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
        legs=legs,
        matchup=matchup,
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
