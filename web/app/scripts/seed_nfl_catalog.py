import argparse
import logging
from typing import Any, Dict, Iterable, Iterator, List

import requests
from requests import HTTPError, RequestException

from ..database import SessionLocal, init_db
from .. import crud


LEAGUES: Dict[str, Dict[str, str]] = {
    "nfl": {
        "sport": "football",
        "name": "NFL",
        "display_name": "National Football League",
        "espn_path": "football/nfl",
    },
    "nba": {
        "sport": "basketball",
        "name": "NBA",
        "display_name": "National Basketball Association",
        "espn_path": "basketball/nba",
    },
    "mlb": {
        "sport": "baseball",
        "name": "MLB",
        "display_name": "Major League Baseball",
        "espn_path": "baseball/mlb",
    },
    "nhl": {
        "sport": "hockey",
        "name": "NHL",
        "display_name": "National Hockey League",
        "espn_path": "hockey/nhl",
    },
}

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def _derive_nickname(team: Dict[str, Any]) -> str | None:
    nickname = team.get("nickname")
    location = team.get("location")
    if nickname and location and nickname.strip().lower() == location.strip().lower():
        nickname = None
    if nickname:
        return nickname
    short = team.get("shortDisplayName")
    if short and (not location or short.strip().lower() != location.strip().lower()):
        return short
    name = team.get("name")
    if name and (not location or name.strip().lower() != location.strip().lower()):
        return name
    display = team.get("displayName")
    if display and location and display.lower().startswith(location.lower()):
        remainder = display[len(location):].strip()
        if remainder:
            return remainder
    return nickname or short or name


def teams_endpoint(league_key: str) -> str:
    config = LEAGUES[league_key]
    return f"https://site.api.espn.com/apis/site/v2/sports/{config['espn_path']}/teams"


def team_detail_endpoint(league_key: str, team_id: str) -> str:
    config = LEAGUES[league_key]
    return f"https://site.api.espn.com/apis/site/v2/sports/{config['espn_path']}/teams/{team_id}"


def fetch_teams(league_key: str) -> List[dict]:
    logger.info("Fetching %s teams from ESPN API…", league_key.upper())
    response = requests.get(
        teams_endpoint(league_key),
        timeout=30,
        headers={"User-Agent": "roach-parlor/seed"},
    )
    response.raise_for_status()
    payload = response.json()
    leagues = payload.get("sports", [{}])[0].get("leagues", [])
    if not leagues:
        raise RuntimeError("Unexpected teams payload structure: missing leagues")
    teams = []
    for wrapper in leagues[0].get("teams", []):
        team = wrapper.get("team", {})
        logos = team.get("logos") or []
        logo_url = logos[0].get("href") if logos else None
        teams.append(
            {
                "external_id": team.get("id"),
                "name": team.get("name"),
                "location": team.get("location"),
                "nickname": _derive_nickname(team),
                "abbreviation": team.get("abbreviation"),
                "logo_url": logo_url,
            }
        )
    logger.info("Found %d teams", len(teams))
    return teams


def _expand_athletes(athletes: Any) -> Iterator[dict]:
    if isinstance(athletes, dict):
        yield from _expand_athletes(athletes.get("items"))
        return
    if not isinstance(athletes, list):
        return
    for entry in athletes:
        if isinstance(entry, dict) and entry.get("items"):
            yield from _expand_athletes(entry.get("items"))
        elif isinstance(entry, dict):
            yield entry


def fetch_roster(league_key: str, team_external_id: str) -> Iterable[dict]:
    url = team_detail_endpoint(league_key, team_external_id)
    response = requests.get(
        url,
        params={"enable": "roster"},
        timeout=30,
        headers={"User-Agent": "roach-parlor/seed"},
    )
    response.raise_for_status()
    payload = response.json()
    team = payload.get("team", {})
    athletes = team.get("athletes") or []
    for athlete in _expand_athletes(athletes):
        if not isinstance(athlete, dict):
            continue
        position = None
        position_info = athlete.get("position") or {}
        if isinstance(position_info, dict):
            position = (
                position_info.get("abbreviation")
                or position_info.get("displayName")
                or position_info.get("name")
            )
        elif isinstance(position_info, str):
            position = position_info

        yield {
            "external_id": athlete.get("id"),
            "first_name": athlete.get("firstName"),
            "last_name": athlete.get("lastName"),
            "full_name": athlete.get("fullName") or athlete.get("displayName"),
            "position": position,
            "jersey_number": athlete.get("jersey"),
        }


def sync_league(db, league_key: str, *, skip_players: bool = False) -> None:
    if league_key not in LEAGUES:
        raise ValueError(f"Unsupported league key '{league_key}'")

    config = LEAGUES[league_key]
    league = crud.upsert_league(
        db,
        key=league_key,
        name=config["name"],
        display_name=config["display_name"],
        sport=config["sport"],
    )
    logger.info("Upserted league %s (id=%s)", league.name, league.id)

    teams = fetch_teams(league_key)
    for team_data in teams:
        team = crud.upsert_team(
            db,
            league_id=league.id,
            external_id=team_data["external_id"],
            name=team_data["name"],
            location=team_data["location"],
            nickname=team_data["nickname"],
            abbreviation=team_data["abbreviation"],
            logo_url=team_data["logo_url"],
        )
        logger.info("Upserted team %s (id=%s)", team_data["name"], team.id)

        if skip_players:
            continue

        external_id = team_data["external_id"]
        if not external_id:
            logger.warning("Skipping roster fetch for %s: missing external id", team.name)
            continue

        try:
            roster = list(fetch_roster(league_key, external_id))
        except (HTTPError, RequestException) as exc:
            logger.warning(
                "Roster fetch failed for %s (%s): %s",
                team.name,
                external_id,
                exc,
            )
            continue

        synced = 0
        for player in roster:
            full_name = player["full_name"]
            if not full_name:
                continue
            crud.upsert_player(
                db,
                team_id=team.id,
                external_id=player["external_id"],
                first_name=player["first_name"],
                last_name=player["last_name"],
                full_name=full_name,
                position=player["position"],
                jersey_number=player["jersey_number"],
            )
            synced += 1
        logger.info("  synced %s players", synced)



def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync teams and players from ESPN into the catalog tables",
    )
    parser.add_argument(
        "--league",
        action="append",
        choices=sorted(LEAGUES.keys()),
        help="League key to sync (may be provided multiple times). Defaults to nfl if omitted.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Sync all supported leagues",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch data without writing to the database",
    )
    parser.add_argument(
        "--skip-players",
        action="store_true",
        help="Only sync leagues and teams (skip player rosters)",
    )
    args = parser.parse_args()

    if args.all:
        leagues = list(LEAGUES.keys())
    elif args.league:
        leagues = args.league
    else:
        leagues = ["nfl"]

    init_db()
    session = SessionLocal()
    try:
        if args.dry_run:
            for league in leagues:
                teams = fetch_teams(league)
                logger.info("[dry-run][%s] Would process %d teams", league, len(teams))
            return

        for league in leagues:
            logger.info("=== Syncing %s ===", league.upper())
            sync_league(session, league, skip_players=args.skip_players)
    finally:
        session.close()


if __name__ == "__main__":
    main()
