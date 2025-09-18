from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, database, schemas, models
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/catalog", tags=["catalog"])


class LeaguePayload(BaseModel):
    key: str
    name: str
    display_name: Optional[str] = None
    sport: Optional[str] = None


class TeamPayload(BaseModel):
    league_id: int
    name: str
    location: Optional[str] = None
    nickname: Optional[str] = None
    abbreviation: Optional[str] = None
    logo_url: Optional[str] = None
    external_id: Optional[str] = None


class PlayerPayload(BaseModel):
    team_id: int
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    jersey_number: Optional[str] = None
    position: Optional[str] = None
    external_id: Optional[str] = None


@router.get("/leagues", response_model=list[schemas.LeagueWithTeams])
def list_leagues(db: Session = Depends(database.get_db)):
    return crud.get_leagues_with_catalog(db)


@router.post("/leagues", response_model=schemas.League)
def upsert_league(payload: LeaguePayload, db: Session = Depends(database.get_db)):
    return crud.upsert_league(
        db,
        key=payload.key,
        name=payload.name,
        display_name=payload.display_name,
        sport=payload.sport,
    )


@router.get("/teams", response_model=list[schemas.TeamWithPlayers])
def list_teams(league_id: int | None = None, db: Session = Depends(database.get_db)):
    return crud.list_teams(db, league_id)


@router.post("/teams", response_model=schemas.Team)
def upsert_team(payload: TeamPayload, db: Session = Depends(database.get_db)):
    return crud.upsert_team(
        db,
        league_id=payload.league_id,
        external_id=payload.external_id,
        name=payload.name,
        location=payload.location,
        nickname=payload.nickname,
        abbreviation=payload.abbreviation,
        logo_url=payload.logo_url,
    )


@router.get("/players", response_model=list[schemas.Player])
def list_players(team_id: int | None = None, db: Session = Depends(database.get_db)):
    return crud.list_players(db, team_id)


@router.post("/players", response_model=schemas.Player)
def upsert_player(payload: PlayerPayload, db: Session = Depends(database.get_db)):
    team = db.query(models.Team).filter(models.Team.id == payload.team_id).one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return crud.upsert_player(
        db,
        team_id=payload.team_id,
        external_id=payload.external_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        full_name=payload.full_name,
        position=payload.position,
        jersey_number=payload.jersey_number,
    )
