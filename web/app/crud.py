import re
from sqlalchemy.orm import Session, selectinload
from . import models


def _prepare_legs(wager: models.Wager, legs: list[dict]):
    wager.legs = []
    for leg in legs:
        desc = (leg.get("description") or "").strip()
        if not desc:
            continue
        status = leg.get("status") or models.WagerLegStatus.open
        if isinstance(status, str):
            try:
                status = models.WagerLegStatus(status)
            except ValueError:
                status = models.WagerLegStatus.open
        wager.legs.append(models.WagerLeg(description=desc, status=status))

# --- User Operations ---
def get_users_with_wagers(db: Session):
    return (
        db.query(models.User)
        .options(
            selectinload(models.User.wagers)
            .selectinload(models.Wager.legs),
            selectinload(models.User.wagers)
            .selectinload(models.Wager.matchup)
            .selectinload(models.WagerMatchup.home_team),
            selectinload(models.User.wagers)
            .selectinload(models.Wager.matchup)
            .selectinload(models.WagerMatchup.away_team),
            selectinload(models.User.wagers)
            .selectinload(models.Wager.matchup)
            .selectinload(models.WagerMatchup.league),
        )
        .order_by(models.User.display_name)
        .all()
    )

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, discord_id: str, display_name: str, profile_pic_url: str = None):
    user = models.User(
        discord_id=discord_id,
        display_name=display_name,
        profile_pic_url=profile_pic_url
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# --- Wager Operations ---
def get_user_wagers(db: Session, user_id: int):
    return db.query(models.Wager).filter(models.Wager.user_id == user_id).all()

def create_wager(
    db: Session,
    user_id: int,
    description: str,
    amount: float,
    line: str,
    legs: list[dict] | None = None,
    matchup: dict | None = None,
):
    wager = models.Wager(user_id=user_id, description=description, amount=amount, line=line)
    if legs:
        _prepare_legs(wager, legs)
    if matchup:
        wager.matchup = models.WagerMatchup(
            league_id=matchup.get("league_id"),
            home_team_id=matchup.get("home_team_id"),
            away_team_id=matchup.get("away_team_id"),
            scheduled_at=matchup.get("scheduled_at"),
        )
    db.add(wager)
    db.commit()
    db.refresh(wager)
    return wager

def update_wager_status(db: Session, wager_id: int, new_status: str):
    wager = db.query(models.Wager).filter(models.Wager.id == wager_id).first()
    if not wager:
        return None

    # Toggle: if same status is clicked again → reset to open
    if wager.status == new_status:
        wager.status = models.WagerStatus.open
    else:
        wager.status = new_status

    db.commit()
    db.refresh(wager)
    return wager


def update_wager_leg_status(db: Session, leg_id: int, new_status: str):
    leg = db.query(models.WagerLeg).filter(models.WagerLeg.id == leg_id).first()
    if not leg:
        return None

    current = leg.status.value if isinstance(leg.status, models.WagerLegStatus) else leg.status
    if current == new_status:
        leg.status = models.WagerLegStatus.open
    else:
        try:
            leg.status = models.WagerLegStatus(new_status)
        except ValueError:
            leg.status = models.WagerLegStatus.open

    db.commit()
    db.refresh(leg)
    return leg
    
def delete_wager(db: Session, wager_id: int):
    wager = db.query(models.Wager).filter(models.Wager.id == wager_id).first()
    if wager:
        db.delete(wager)
        db.commit()
    return wager


# --- League / Team / Player Operations ---


def upsert_league(
    db: Session,
    *,
    key: str,
    name: str,
    display_name: str | None = None,
    sport: str | None = None,
) -> models.League:
    league = (
        db.query(models.League)
        .filter(models.League.key == key)
        .one_or_none()
    )
    if not league:
        league = models.League(key=key, name=name)
        db.add(league)
    league.name = name or league.name
    league.display_name = display_name or league.display_name
    league.sport = sport or league.sport
    db.commit()
    db.refresh(league)
    return league


def upsert_team(
    db: Session,
    *,
    league_id: int,
    external_id: str | None = None,
    name: str,
    location: str | None = None,
    nickname: str | None = None,
    abbreviation: str | None = None,
    logo_url: str | None = None,
) -> models.Team:
    query = db.query(models.Team).filter(models.Team.league_id == league_id)
    if external_id:
        query = query.filter(models.Team.external_id == external_id)
    elif abbreviation:
        query = query.filter(models.Team.abbreviation == abbreviation)
    else:
        query = query.filter(models.Team.name == name)

    team = query.one_or_none()
    if not team:
        team = models.Team(league_id=league_id, name=name)
        db.add(team)

    team.external_id = external_id or team.external_id
    team.location = location or team.location
    team.name = name or team.name
    team.nickname = nickname or team.nickname
    team.abbreviation = abbreviation or team.abbreviation
    team.logo_url = logo_url or team.logo_url

    db.commit()
    db.refresh(team)
    return team


def upsert_player(
    db: Session,
    *,
    team_id: int,
    external_id: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    full_name: str,
    position: str | None = None,
    jersey_number: str | None = None,
) -> models.Player:
    query = db.query(models.Player).filter(models.Player.team_id == team_id)
    if external_id:
        query = query.filter(models.Player.external_id == external_id)
    else:
        query = query.filter(models.Player.full_name == full_name)

    player = query.one_or_none()
    if not player:
        player = models.Player(team_id=team_id, full_name=full_name)
        db.add(player)

    player.external_id = external_id or player.external_id
    player.first_name = first_name or player.first_name
    player.last_name = last_name or player.last_name
    player.full_name = full_name or player.full_name
    player.position = position or player.position
    player.jersey_number = jersey_number or player.jersey_number

    db.commit()
    db.refresh(player)
    return player


def get_leagues_with_catalog(db: Session):
    return (
        db.query(models.League)
        .options(
            selectinload(models.League.teams)
            .selectinload(models.Team.players),
        )
        .order_by(models.League.name)
        .all()
    )


def list_teams(db: Session, league_id: int | None = None):
    query = db.query(models.Team).options(selectinload(models.Team.players))
    if league_id is not None:
        query = query.filter(models.Team.league_id == league_id)
    return query.order_by(models.Team.name).all()


def list_players(db: Session, team_id: int | None = None):
    query = db.query(models.Player)
    if team_id is not None:
        query = query.filter(models.Player.team_id == team_id)
    return query.order_by(models.Player.full_name).all()


_alias_cleanup = re.compile(r"[^a-z0-9]")


def _normalize_alias(value: str) -> str:
    return _alias_cleanup.sub("", value.lower())


def build_team_alias_lookup(db: Session) -> dict[str, models.Team]:
    teams = db.query(models.Team).all()
    lookup: dict[str, models.Team] = {}
    for team in teams:
        aliases: list[str] = []
        for attr in (
            "external_id",
            "abbreviation",
            "nickname",
            "name",
            "display_name",
            "location",
        ):
            value = getattr(team, attr, None)
            if value:
                aliases.append(str(value))
        if team.location and team.nickname:
            aliases.append(f"{team.location} {team.nickname}")
        if team.location and team.name:
            aliases.append(f"{team.location} {team.name}")

        for alias in aliases:
            normalized = _normalize_alias(alias)
            if len(normalized) < 3:
                continue
            lookup.setdefault(normalized, team)
    return lookup


def match_leg_description_to_teams(description: str, lookup: dict[str, models.Team]) -> list[models.Team]:
    if not description:
        return []
    normalized_text = _normalize_alias(description)
    if not normalized_text:
        return []

    matches: list[models.Team] = []
    seen_ids: set[int] = set()
    for alias, team in lookup.items():
        if alias in normalized_text and team.id not in seen_ids:
            matches.append(team)
            seen_ids.add(team.id)
    return matches
