import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
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
    users = (
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

    def sort_wagers(wager_list: list[models.Wager]):
        def created_key(wager: models.Wager):
            created = getattr(wager, "created_at", None)
            if isinstance(created, datetime):
                return created
            if isinstance(created, str):
                try:
                    return datetime.fromisoformat(created)
                except ValueError:
                    return datetime.min
            return datetime.min

        return sorted(wager_list, key=created_key, reverse=True)

    for user in users:
        active = [wager for wager in user.wagers if not getattr(wager, "archived", False)]
        archived = [wager for wager in user.wagers if getattr(wager, "archived", False)]
        active_sorted = sort_wagers(active)
        archived_sorted = sort_wagers(archived)
        setattr(user, "active_wagers", active_sorted)
        setattr(user, "archived_wagers", archived_sorted)

    return users

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


def set_user_tracked(db: Session, user_id: int, tracked: bool):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None
    user.tracked = tracked
    db.commit()
    db.refresh(user)
    return user


# --- Auth Users ---


def get_auth_user_by_id(db: Session, user_id: int):
    return db.query(models.AuthUser).filter(models.AuthUser.id == user_id).one_or_none()


def get_auth_user_by_username(db: Session, username: str):
    return (
        db.query(models.AuthUser)
        .filter(models.AuthUser.username == username)
        .one_or_none()
    )


def create_auth_user(
    db: Session,
    *,
    username: str,
    password_hash: str,
    salt: str,
    is_admin: bool = False,
):
    user = models.AuthUser(
        username=username,
        password_hash=password_hash,
        salt=salt,
        is_admin=is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_auth_user_password(
    db: Session,
    user_id: int,
    *,
    password_hash: str,
    salt: str,
):
    user = db.query(models.AuthUser).filter(models.AuthUser.id == user_id).one_or_none()
    if not user:
        return None
    user.password_hash = password_hash
    user.salt = salt
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
    is_free_play: bool = False,
    legs: list[dict] | None = None,
    matchup: dict | None = None,
    archived: bool = False,
    discord_message_id: str | None = None,
    discord_channel_id: str | None = None,
):
    try:
        amount_value = Decimal(str(amount)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError):
        amount_value = Decimal("0.00")

    wager = models.Wager(
        user_id=user_id,
        description=description,
        amount=amount_value,
        line=line,
        is_free_play=bool(is_free_play),
        archived=archived,
        discord_message_id=discord_message_id,
        discord_channel_id=discord_channel_id,
    )
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


def set_wager_archived(db: Session, wager_id: int, archived: bool):
    wager = db.query(models.Wager).filter(models.Wager.id == wager_id).first()
    if not wager:
        return None

    previous_archived = bool(wager.archived)
    wager.archived = archived
    if archived and not previous_archived:
        wager.archive_reacted = False
    elif not archived and previous_archived:
        wager.archive_reacted = False

    db.commit()
    db.refresh(wager)
    return wager


def archive_decided_wagers(db: Session) -> int:
    """Archive wagers that have been decided but remain active."""
    query = (
        db.query(models.Wager)
        .filter(models.Wager.archived.is_(False))
        .filter(models.Wager.status.in_([models.WagerStatus.won, models.WagerStatus.lost]))
    )

    archived_count = 0
    for wager in query.all():
        wager.archived = True
        wager.archive_reacted = False
        archived_count += 1

    if archived_count:
        db.commit()

    return archived_count


def get_archived_wagers_pending_reaction(db: Session, *, limit: int = 50):
    query = (
        db.query(models.Wager)
        .filter(models.Wager.archived.is_(True))
        .filter(models.Wager.archive_reacted.is_(False))
        .order_by(models.Wager.created_at.asc())
    )
    if limit:
        query = query.limit(limit)
    return query.all()


def mark_wager_archive_reacted(db: Session, wager_id: int, reacted: bool = True):
    wager = db.query(models.Wager).filter(models.Wager.id == wager_id).first()
    if not wager:
        return None

    wager.archive_reacted = bool(reacted)
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


def update_wager_details(
    db: Session,
    wager_id: int,
    *,
    description: str | None = None,
    amount: float | str | None = None,
    line: str | None = None,
    status: str | None = None,
    archived: bool | None = None,
    is_free_play: bool | None = None,
    created_at: datetime | None = None,
):
    wager = db.query(models.Wager).filter(models.Wager.id == wager_id).first()
    if not wager:
        return None

    if description is not None:
        wager.description = description

    if amount is not None:
        try:
            amount_value = Decimal(str(amount)).quantize(Decimal("0.01"))
            wager.amount = amount_value
        except (InvalidOperation, TypeError):
            pass

    if line is not None:
        wager.line = line

    if status is not None:
        try:
            wager.status = models.WagerStatus(status)
        except ValueError:
            pass

    if archived is not None:
        wager.archived = bool(archived)

    if is_free_play is not None:
        wager.is_free_play = bool(is_free_play)

    if created_at is not None:
        wager.created_at = created_at

    db.commit()
    db.refresh(wager)
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


def build_team_alias_lookup(db: Session) -> list[dict[str, object]]:
    teams = db.query(models.Team).all()
    entries: list[dict[str, object]] = []

    for team in teams:
        seen: set[str] = set()

        def add_alias(alias: str | None, *, strict: bool = False):
            if not alias:
                return
            normalized = _normalize_alias(alias)
            if len(normalized) < 3:
                return
            key = (team.id, normalized)
            if key in seen:
                return
            seen.add(key)
            entries.append(
                {
                    "team": team,
                    "alias": alias,
                    "normalized": normalized,
                    "strict": strict,
                }
            )

        add_alias(team.external_id, strict=True)
        add_alias(team.abbreviation, strict=True)
        add_alias(team.nickname)
        add_alias(team.name)
        add_alias(team.display_name)

        if team.location and team.nickname:
            add_alias(f"{team.location} {team.nickname}")
        if team.location and team.name:
            add_alias(f"{team.location} {team.name}")

    return entries


def match_leg_description_to_teams(description: str, aliases: list[dict[str, object]]) -> list[models.Team]:
    if not description:
        return []

    normalized_text = _normalize_alias(description)
    if not normalized_text:
        return []

    lower_text = description.lower()
    best: dict[int, tuple[float, models.Team]] = {}

    for entry in aliases:
        team: models.Team = entry["team"]  # type: ignore[assignment]
        normalized_alias: str = entry["normalized"]  # type: ignore[assignment]
        alias_text: str = str(entry["alias"]).lower()
        strict: bool = bool(entry["strict"])  # type: ignore[assignment]

        if normalized_alias not in normalized_text:
            continue

        pattern = rf"\b{re.escape(alias_text)}\b"
        if strict:
            if not re.search(pattern, lower_text):
                continue
        elif len(normalized_alias) <= 5:
            if not re.search(pattern, lower_text):
                continue

        score = len(normalized_alias)
        if alias_text in lower_text:
            score += 5

        location = (team.location or "").lower()
        if location and location in lower_text:
            score += 3

        nickname = (team.nickname or "").lower()
        if nickname and nickname in lower_text:
            score += 4

        display = (team.display_name or "").lower()
        if display and display in lower_text:
            score += 6

        current = best.get(team.id)
        if not current or score > current[0]:
            best[team.id] = (score, team)

    ranked = sorted(best.values(), key=lambda item: item[0], reverse=True)
    return [team for _, team in ranked[:2]]
