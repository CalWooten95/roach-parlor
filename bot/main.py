import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import discord
import requests

# --- Config ---
API_URL = os.getenv("API_URL", "http://web:8000")  # docker uses http://web:8000; locally http://localhost:8000
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "lv-raiders-test")
WEB_UI_URL = os.getenv("WEB_UI_URL")

# --- OpenAI (Responses API) ---
try:
    from openai import OpenAI

    _openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
    if _openai_client:
        print("OpenAI client initialized.")
except Exception:  # pragma: no cover - defensive fallback
    _openai_client = None

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

CATALOG_TTL_SECONDS = 60 * 15
LIVE_PREFIX = "🚨 LIVE 🚨 "
_catalog_cache: Dict[str, Any] = {
    "expires": 0.0,
    "leagues_by_key": {},
    "team_lookup": {},  # league_id -> {normalized_alias: team_dict}
}


def _user_payload_from_discord(author: discord.User | discord.Member) -> Dict[str, Optional[str]]:
    discord_id = str(author.id)
    display_name = getattr(author, "display_name", author.name)
    avatar_url = str(author.display_avatar.url) if author.display_avatar else None
    return {
        "discord_id": discord_id,
        "display_name": display_name,
        "profile_pic_url": avatar_url,
    }


def ensure_user_and_get_id(author: discord.User | discord.Member) -> int:
    payload = _user_payload_from_discord(author)
    response = requests.post(f"{API_URL}/users/", json=payload, timeout=10)
    if response.status_code == 200:
        return response.json()["id"]
    if response.status_code == 400:
        lookup = requests.get(f"{API_URL}/users/", timeout=10)
        lookup.raise_for_status()
        for user in lookup.json():
            if user["discord_id"] == payload["discord_id"]:
                return user["id"]
    response.raise_for_status()
    raise RuntimeError("Failed to ensure user exists")


SYSTEM_PROMPT = (
    "You extract structured data from sports wager screenshots. "
    "Return STRICT JSON with keys: description (string), amount (number), line (string), legs (array), "
    "league_key (string), home_team (object|null), away_team (object|null), is_live_bet (boolean). "
    "Each leg object must contain description (string) and status (open|won|lost). "
    "Default status is 'open' unless the ticket clearly shows otherwise. "
    "- For parlays: include one leg per selection with concise descriptions. "
    "  When the ticket contains multiple independent selections, set home_team and away_team to null. "
    "- For single bets: still include one leg describing the wager. "
    "- For player props: include player, stat, and threshold in the leg description. "
    "- Amount must be the stake ('Risk'). "
    "- When the slip shows both 'Risk' and 'Win' or 'To Win', always derive the American odds from those values "
    "  (treat 'Win' as profit, not total payout). If Win >= Risk, line = +(Win / Risk * 100); otherwise line = -(Risk / Win * 100). "
    "  After computing, round to the nearest 5 and clamp positive odds to at least +100 and negative odds to at most -100. "
    "  Ignore any conflicting odds text on the ticket if the calculation can be made. "
    "- Return league_key as nfl, nba, mlb, nhl when clear; otherwise use an empty string. "
    "- home_team/away_team should include as many keys as visible: name, abbreviation, short_name, location, nickname, external_id. "
    "  Use null when a team is unknown. "
    "- If a field is unknown, set it to an empty string (line) or 0 (amount). "
    "- If the ticket indicates a live wager (labels such as 'LIVE' or 'LIVE BET'), set is_live_bet to true; otherwise false. "
    "- You may also receive extra context text from the user alongside the screenshot; treat it as a reliable hint and make reasonable inferences from it when the slip itself is ambiguous. "
    "Do not add any extra keys or text."
)


def parse_wager_from_image(image_url: str, *, extra_context: str | None = None) -> Dict[str, Any]:
    if _openai_client is None:
        raise RuntimeError("OpenAI client not initialized. Set OPENAI_API_KEY.")

    content_blocks = [{"type": "input_text", "text": SYSTEM_PROMPT}]
    if extra_context:
        content_blocks.append(
            {
                "type": "input_text",
                "text": f"Additional context supplied with the command: {extra_context}",
            }
        )
    content_blocks.append({"type": "input_image", "image_url": image_url})

    response = _openai_client.responses.create(
        model="gpt-4o-mini",
        input=[{"role": "user", "content": content_blocks}],
    )

    text = getattr(response, "output_text", None)
    if not text:
        try:
            parts = []
            for item in response.output[0].content:
                if item.get("type") == "output_text":
                    parts.append(item.get("text", ""))
            text = "\n".join(parts)
        except Exception:  # pragma: no cover - defensive fallback
            text = ""

    try:
        data = json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise RuntimeError(f"Model did not return JSON. Raw text:\n{text}")
        data = json.loads(match.group(0))

    description = str(data.get("description") or "").strip()
    line = str(data.get("line") or "").strip()
    try:
        amount = float(data.get("amount") or 0)
    except Exception:
        amount = 0.0

    is_live_raw = data.get("is_live_bet")
    if isinstance(is_live_raw, bool):
        is_live_bet = is_live_raw
    elif isinstance(is_live_raw, str):
        is_live_bet = is_live_raw.strip().lower() in {"true", "yes", "1"}
    else:
        is_live_bet = False

    raw_legs = data.get("legs") or []
    legs: List[Dict[str, str]] = []
    for leg in raw_legs:
        if not isinstance(leg, dict):
            continue
        leg_description = str(leg.get("description") or "").strip()
        if not leg_description:
            continue
        leg_status = str(leg.get("status") or "open").lower().strip()
        if leg_status not in {"open", "won", "lost"}:
            leg_status = "open"
        legs.append({"description": leg_description, "status": leg_status})

    # Single straight bets shouldn't create a leg entry—keep legs for true multi-leg wagers only.
    if len(legs) == 1:
        legs = []

    searchable_text_parts = [description, line]
    searchable_text_parts.extend(leg["description"] for leg in legs)
    if extra_context:
        searchable_text_parts.append(extra_context)
    searchable_text = " ".join(filter(None, searchable_text_parts))
    if not is_live_bet and re.search(r"\blive(\s+bet)?\b", searchable_text, flags=re.I):
        is_live_bet = True
    if not is_live_bet and text and re.search(r"\blive(\s+bet)?\b", text, flags=re.I):
        is_live_bet = True

    league_key = str(data.get("league_key") or data.get("league") or "").strip().lower()

    def _team_dict(raw: Any) -> Dict[str, str]:
        if raw is None:
            return {}
        if isinstance(raw, str):
            return {"name": raw}
        if isinstance(raw, dict):
            return {k: v for k, v in raw.items() if isinstance(k, str) and v}
        return {}

    home_team = _team_dict(data.get("home_team"))
    away_team = _team_dict(data.get("away_team"))

    return {
        "description": description,
        "amount": amount,
        "line": line,
        "legs": legs,
        "league_key": league_key,
        "home_team": home_team,
        "away_team": away_team,
        "is_live_bet": is_live_bet,
    }


def _normalize_alias(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _load_catalog(force: bool = False) -> None:
    now = time.time()
    if not force and now < _catalog_cache["expires"]:
        return

    leagues_resp = requests.get(f"{API_URL}/catalog/leagues", timeout=10)
    leagues_resp.raise_for_status()
    leagues = leagues_resp.json()

    leagues_by_key: Dict[str, Dict[str, Any]] = {}
    team_lookup: Dict[int, Dict[str, Dict[str, Any]]] = {}

    for league in leagues:
        league_id = league["id"]
        key = (league.get("key") or "").lower()
        if key:
            leagues_by_key[key] = league

        teams_resp = requests.get(
            f"{API_URL}/catalog/teams",
            params={"league_id": league_id},
            timeout=10,
        )
        teams_resp.raise_for_status()
        teams = teams_resp.json()

        lookup: Dict[str, Dict[str, Any]] = {}
        for team in teams:
            aliases: List[str] = []
            for field in (
                "external_id",
                "abbreviation",
                "nickname",
                "name",
                "display_name",
                "location",
            ):
                value = team.get(field)
                if value:
                    aliases.append(str(value))
            if team.get("location") and team.get("nickname"):
                aliases.append(f"{team['location']} {team['nickname']}")
            if team.get("location") and team.get("name"):
                aliases.append(f"{team['location']} {team['name']}")

            for alias in aliases:
                normalized = _normalize_alias(alias)
                if normalized and normalized not in lookup:
                    lookup[normalized] = team

        team_lookup[league_id] = lookup

    _catalog_cache.update(
        {
            "expires": now + CATALOG_TTL_SECONDS,
            "leagues_by_key": leagues_by_key,
            "team_lookup": team_lookup,
        }
    )


def _resolve_team_id(league_key: str, team_data: Dict[str, str]) -> Optional[int]:
    if not league_key or not team_data:
        return None

    _load_catalog()
    league = _catalog_cache["leagues_by_key"].get(league_key.lower())
    if not league:
        return None

    lookup = _catalog_cache["team_lookup"].get(league["id"], {})
    candidates: List[str] = []

    for field in (
        "external_id",
        "abbreviation",
        "short_name",
        "nickname",
        "name",
        "display_name",
        "location",
    ):
        value = team_data.get(field)
        if value:
            candidates.append(str(value))
    if team_data.get("location") and team_data.get("nickname"):
        candidates.append(f"{team_data['location']} {team_data['nickname']}")
    if team_data.get("location") and team_data.get("name"):
        candidates.append(f"{team_data['location']} {team_data['name']}")

    for candidate in candidates:
        normalized = _normalize_alias(candidate)
        team = lookup.get(normalized)
        if team:
            return team["id"]

    for candidate in candidates:
        normalized = _normalize_alias(candidate)
        if not normalized:
            continue
        for alias, team in lookup.items():
            if normalized in alias or alias in normalized:
                return team["id"]

    return None


def resolve_matchup_ids(parsed: Dict[str, Any]) -> Tuple[Optional[Dict[str, int]], List[str]]:
    notes: List[str] = []
    league_key = parsed.get("league_key") or ""
    if not league_key:
        notes.append("league not identified")
        return None, notes

    if len(parsed.get("legs") or []) > 1:
        notes.append("multiple legs — no single matchup")
        return None, notes

    home_id = _resolve_team_id(league_key, parsed.get("home_team") or {})
    away_id = _resolve_team_id(league_key, parsed.get("away_team") or {})

    missing: List[str] = []
    if not home_id:
        missing.append("home team")
    if not away_id:
        missing.append("away team")

    if missing:
        notes.append("could not map " + ", ".join(missing))
        return None, notes

    league = _catalog_cache["leagues_by_key"].get(league_key.lower())
    if not league:
        notes.append("league not in catalog")
        return None, notes

    matchup = {
        "league_id": league["id"],
        "home_team_id": home_id,
        "away_team_id": away_id,
    }

    return matchup, notes


def create_wager(
    user_id: int,
    description: str,
    amount: float,
    line: str,
    legs: Optional[List[Dict[str, str]]] = None,
    matchup: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "user_id": user_id,
        "description": description,
        "amount": amount,
        "line": line,
        "legs": legs or [],
    }
    if matchup:
        payload["matchup"] = matchup
    response = requests.post(f"{API_URL}/wagers/", json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    if isinstance(message.channel, (discord.TextChannel, discord.Thread)) and getattr(message.channel, "name", "") != TARGET_CHANNEL:
        return

    raw_content = message.content.strip()
    parts = raw_content.split(maxsplit=1) if raw_content else []
    command = parts[0].lower() if parts else ""

    if command == "!track":
        if not message.attachments:
            await message.channel.send("❌ Please attach a **screenshot** of the bet with the `!track` command.")
            return

        image = None
        for attachment in message.attachments:
            content_type = (attachment.content_type or "").lower()
            if "image" in content_type or attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                image = attachment
                break

        if not image:
            await message.channel.send("❌ I didn't find an image attachment. Please attach a screenshot (PNG/JPG).")
            return

        try:
            user_id = ensure_user_and_get_id(message.author)
            await message.channel.send("🧐 Reading your screenshot…")

            extra_context = parts[1].strip() if len(parts) > 1 else ""
            parsed = parse_wager_from_image(image.url, extra_context=extra_context)
            description = parsed["description"] or "Bet (screenshot)"
            if parsed.get("is_live_bet") and not description.strip().startswith(LIVE_PREFIX.strip()):
                description = f"{LIVE_PREFIX}{description}"
            amount = float(parsed["amount"] or 0)
            line = parsed["line"] or ""

            matchup, matchup_notes = resolve_matchup_ids(parsed)
            _ = create_wager(
                user_id=user_id,
                description=description,
                amount=amount,
                line=line,
                legs=parsed["legs"],
                matchup=matchup,
            )

            leg_lines = "\n".join(f"    - {leg['description']} ({leg['status']})" for leg in parsed["legs"])
            summary = (
                f"**Tracked!**\n• **Desc:** {description}\n"
                f"• **Amount:** ${amount:.2f}\n"
                f"• **Line:** {line or '(unknown)'}"
            )
            if leg_lines:
                summary += f"\n• **Legs:**\n{leg_lines}"
            if matchup_notes:
                summary += "\n• Matchup mapping: " + "; ".join(matchup_notes)
            if WEB_UI_URL:
                summary += f"\nTracker UI: {WEB_UI_URL}"
            await message.channel.send(summary)

        except requests.HTTPError as http_err:
            await message.channel.send(f"❌ API error: {http_err.response.status_code} {http_err.response.text}")
        except Exception as exc:
            await message.channel.send(f"❌ Sorry, I couldn't process that: `{exc}`. Try again or post a clearer screenshot.")


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise SystemExit("Missing DISCORD_TOKEN")
    if not API_URL:
        raise SystemExit("Missing API_URL")
    if not OPENAI_API_KEY:
        print("⚠️  Warning: OPENAI_API_KEY not set. !track will fail on parsing.")
    client.run(DISCORD_TOKEN)
