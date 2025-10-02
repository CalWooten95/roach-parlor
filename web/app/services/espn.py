from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, List

import requests

logger = logging.getLogger(__name__)

_BASE_URL_TEMPLATE = "https://site.api.espn.com/apis/site/v2/sports/{}/scoreboard"

SUPPORTED_LEAGUES: Dict[str, str] = {
    "nfl": "football/nfl",
    "nba": "basketball/nba",
    "nhl": "hockey/nhl",
    "mlb": "baseball/mlb",
}

DEFAULT_LEAGUE = "nfl"


class ESPNFetchError(RuntimeError):
    """Raised when the ESPN API cannot be reached."""


@dataclass(slots=True)
class TeamSide:
    name: str
    abbreviation: str | None
    logo: str | None
    record: str | None
    score: str | None
    is_home: bool
    espn_id: str | None = None
    moneyline: float | None = None
    spread: float | None = None
    spread_odds: float | None = None
    favorite: bool | None = None


@dataclass(slots=True)
class GameCard:
    event_id: str
    name: str
    short_name: str
    status: str
    status_detail: str
    start_time: datetime | None
    venue: str | None
    networks: List[str]
    teams: List[TeamSide]
    odds: GameOdds | None = None


@dataclass(slots=True)
class DaySchedule:
    day: date
    games: List[GameCard]


@dataclass(slots=True)
class GameOdds:
    provider: str | None
    details: str | None
    spread: float | None
    over_under: float | None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    cleaned = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        logger.debug("Failed to parse datetime from %s", value)
        return None


def _extract_record(competitor: dict) -> str | None:
    records = competitor.get("records") or []
    for record in records:
        summary = record.get("summary")
        if summary:
            return summary
    return None


def _extract_networks(competition: dict) -> List[str]:
    broadcasts = competition.get("broadcasts") or []
    networks: List[str] = []
    for broadcast in broadcasts:
        name = broadcast.get("name") or broadcast.get("shortName")
        if name:
            networks.append(name)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: List[str] = []
    for item in networks:
        if item not in seen:
            unique.append(item)
            seen.add(item)
    return unique


def _convert_event(event: dict) -> GameCard | None:
    competitions = event.get("competitions") or []
    if not competitions:
        return None
    competition = competitions[0]
    status = competition.get("status") or event.get("status") or {}
    status_type = status.get("type") or {}

    competitors: Iterable[dict] = competition.get("competitors") or []
    teams: List[TeamSide] = []
    for competitor in competitors:
        team = competitor.get("team") or {}
        logo = None
        logos = team.get("logos")
        if isinstance(logos, list) and logos:
            for entry in logos:
                if not isinstance(entry, dict):
                    continue
                logo = entry.get("href") or entry.get("url") or entry.get("src")
                if logo:
                    break
        if not logo:
            logo = team.get("logo")

        teams.append(
            TeamSide(
                name=team.get("displayName") or team.get("name") or "",
                abbreviation=team.get("abbreviation"),
                logo=logo,
                record=_extract_record(competitor),
                score=competitor.get("score"),
                is_home=competitor.get("homeAway") == "home",
                espn_id=str(team.get("id")) if team.get("id") is not None else None,
            )
        )

    odds_entries = competition.get("odds") or []
    game_odds: GameOdds | None = None
    if odds_entries:
        primary = min(
            odds_entries,
            key=lambda item: (item.get("provider", {}).get("priority") or 99),
        )
        provider_info = primary.get("provider") or {}
        game_odds = GameOdds(
            provider=provider_info.get("name"),
            details=primary.get("details"),
            spread=primary.get("spread"),
            over_under=primary.get("overUnder"),
        )

        spread_value = primary.get("spread")

        def apply_team_odds(odds_entry: dict | None, *, is_home: bool):
            if not odds_entry:
                return
            team_info = odds_entry.get("team") or {}
            team_id = team_info.get("id")
            abbreviation = team_info.get("abbreviation")
            target: TeamSide | None = None
            if team_id is not None:
                needle = str(team_id)
                for candidate in teams:
                    if candidate.espn_id == needle:
                        target = candidate
                        break
            if target is None and abbreviation:
                for candidate in teams:
                    if candidate.abbreviation == abbreviation:
                        target = candidate
                        break
            if target is None:
                for candidate in teams:
                    if candidate.is_home == is_home:
                        target = candidate
                        break
            if target is None:
                return
            try:
                target.moneyline = float(odds_entry.get("moneyLine"))
            except (TypeError, ValueError):
                target.moneyline = None

            if spread_value is not None:
                try:
                    spread_val = float(spread_value)
                    if odds_entry.get("favorite"):
                        target.spread = spread_val
                    elif spread_val is not None:
                        target.spread = -spread_val
                except (TypeError, ValueError):
                    target.spread = None

            try:
                target.spread_odds = float(odds_entry.get("spreadOdds"))
            except (TypeError, ValueError):
                target.spread_odds = None

            favorite = odds_entry.get("favorite")
            if favorite is not None:
                target.favorite = bool(favorite)

        apply_team_odds(primary.get("homeTeamOdds"), is_home=True)
        apply_team_odds(primary.get("awayTeamOdds"), is_home=False)

    return GameCard(
        event_id=str(event.get("id")),
        name=event.get("name") or "",
        short_name=event.get("shortName") or "",
        status=status_type.get("name") or status.get("type") or "UNKNOWN",
        status_detail=status_type.get("shortDetail")
        or status_type.get("detail")
        or status.get("displayClock")
        or "",
        start_time=_parse_datetime(event.get("date")),
        venue=(competition.get("venue") or {}).get("fullName"),
        networks=_extract_networks(competition),
        teams=teams,
        odds=game_odds,
    )


def _fetch_day_schedule(league: str, day: date) -> List[GameCard]:
    if league not in SUPPORTED_LEAGUES:
        raise ValueError(f"Unsupported league: {league}")

    path = SUPPORTED_LEAGUES[league]
    url = _BASE_URL_TEMPLATE.format(path)
    params = {"dates": day.strftime("%Y%m%d")}

    try:
        response = requests.get(url, params=params, timeout=10)
    except requests.RequestException as exc:
        logger.warning("ESPN request failed for %s %s: %s", league, day, exc)
        raise ESPNFetchError(str(exc)) from exc

    if not response.ok:
        logger.warning(
            "ESPN request returned %s for %s %s",
            response.status_code,
            league,
            day,
        )
        raise ESPNFetchError(f"HTTP {response.status_code}")

    payload = response.json()
    events = payload.get("events") or []

    games: List[GameCard] = []
    for event in events:
        card = _convert_event(event)
        if card:
            games.append(card)
    return games


def fetch_week_schedule(league: str, start_day: date) -> List[DaySchedule]:
    """Return a seven day schedule window for the requested league."""
    schedules: List[DaySchedule] = []
    current = start_day
    for _ in range(7):
        try:
            games = _fetch_day_schedule(league, current)
        except ESPNFetchError:
            logger.exception("Failed to load ESPN schedule for %s on %s", league, current)
            games = []
        schedules.append(DaySchedule(day=current, games=games))
        current += timedelta(days=1)
    return schedules
