import asyncio
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
ARCHIVE_POLL_SECONDS = int(os.getenv("ARCHIVE_POLL_SECONDS", "30"))
_catalog_cache: Dict[str, Any] = {
    "expires": 0.0,
    "leagues_by_key": {},
    "team_lookup": {},  # league_id -> {normalized_alias: team_dict}
}

_archive_poll_task: Optional[asyncio.Task] = None


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
    "league_key (string), home_team (object|null), away_team (object|null), is_live_bet (boolean), "
    "is_free_play (boolean). "
    "Each leg object must contain description (string) and status (open|won|lost). "
    "Default status is 'open' unless the ticket clearly shows otherwise. "
    "- For parlays: include one leg per selection with concise descriptions. "
    "  When the ticket contains multiple independent selections, set home_team and away_team to null. "
    "- For single bets: still include one leg describing the wager. "
    "- For player props: include player, stat, and threshold in the leg description. "
    "- Amount must be the stake ('Risk'). "
    "- Set is_free_play to true when the ticket or accompanying text clearly marks the wager as a free play, "
    "  free bet, bonus bet, or similar; otherwise false. Free play wagers still include the stake amount shown on the slip. "
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

    free_play_raw = data.get("is_free_play")
    if isinstance(free_play_raw, bool):
        is_free_play = free_play_raw
    elif isinstance(free_play_raw, str):
        is_free_play = free_play_raw.strip().lower() in {"true", "yes", "1"}
    else:
        is_free_play = None

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

    def _contains_free_play(value: str | None) -> bool:
        if not value:
            return False
        return bool(
            re.search(
                r"\bfree\s*play\b|\bfree\s*bet\b|\bbonus\s*bet\b|\bbonus\s*wager\b",
                value,
                flags=re.I,
            )
        )

    fallback_free_play = any(
        _contains_free_play(piece)
        for piece in (
            description,
            line,
            " ".join(leg["description"] for leg in legs),
            extra_context,
            searchable_text,
            text,
        )
    )

    if is_free_play is None:
        is_free_play = fallback_free_play
    elif not is_free_play and fallback_free_play:
        is_free_play = True

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
        "is_free_play": bool(is_free_play),
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
    is_free_play: bool = False,
    legs: Optional[List[Dict[str, str]]] = None,
    matchup: Optional[Dict[str, int]] = None,
    discord_message_id: Optional[str] = None,
    discord_channel_id: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "user_id": user_id,
        "description": description,
        "amount": amount,
        "line": line,
        "is_free_play": bool(is_free_play),
        "legs": legs or [],
    }
    if matchup:
        payload["matchup"] = matchup
    if discord_message_id:
        payload["discord_message_id"] = discord_message_id
    if discord_channel_id:
        payload["discord_channel_id"] = discord_channel_id
    response = requests.post(f"{API_URL}/wagers/", json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_archived_wagers_pending(limit: int = 25) -> List[Dict[str, Any]]:
    response = requests.get(
        f"{API_URL}/wagers/archive/pending",
        params={"limit": limit},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        return []
    return data


def mark_wager_archive_reacted_api(wager_id: int, reacted: bool = True) -> bool:
    try:
        response = requests.post(
            f"{API_URL}/wagers/{wager_id}/archive/reacted",
            json={"reacted": bool(reacted)},
            timeout=10,
        )
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        print(f"Archive reaction: failed to mark wager {wager_id} as reacted: {exc}")
        return False


def _reaction_emoji_for_status(status: Optional[str]) -> str:
    if isinstance(status, str) and status.lower() == "won":
        return "✅"
    return "❌"


async def _react_to_archived_wager(wager: Dict[str, Any]) -> None:
    wager_id = wager.get("id")
    if wager_id is None:
        return

    message_id = wager.get("discord_message_id")
    channel_id = wager.get("discord_channel_id")
    emoji = _reaction_emoji_for_status(wager.get("status"))

    success = False
    if message_id and channel_id:
        try:
            channel_int = int(channel_id)
            message_int = int(message_id)
        except (TypeError, ValueError):
            print(
                f"Archive reaction: invalid Discord IDs for wager {wager_id}"
            )
            mark_wager_archive_reacted_api(wager_id)
            return

        channel = client.get_channel(channel_int)
        if channel is None:
            try:
                channel = await client.fetch_channel(channel_int)
            except Exception as exc:
                print(
                    f"Archive reaction: could not fetch channel {channel_id} for wager {wager_id}: {exc}"
                )
                channel = None

        if channel is not None:
            try:
                message = await channel.fetch_message(message_int)
                await message.add_reaction(emoji)
                success = True
            except Exception as exc:
                print(
                    f"Archive reaction: failed to react to wager {wager_id} message {message_id}: {exc}"
                )
        else:
            print(
                f"Archive reaction: unable to locate channel {channel_id} for wager {wager_id}"
            )
    else:
        print(
            f"Archive reaction: wager {wager_id} missing Discord metadata; skipping reaction"
        )

    if not mark_wager_archive_reacted_api(wager_id):
        # Leave for the next polling cycle if the backend update failed
        return

    if not success:
        print(
            f"Archive reaction: wager {wager_id} marked as reacted without adding emoji"
        )


async def _archive_reaction_poller() -> None:
    await client.wait_until_ready()
    interval = ARCHIVE_POLL_SECONDS if ARCHIVE_POLL_SECONDS > 0 else 60

    while not client.is_closed():
        try:
            pending = fetch_archived_wagers_pending()
        except Exception as exc:  # pragma: no cover - defensive
            print(f"Archive reaction poller error: {exc}")
            pending = []

        for wager in pending:
            try:
                await _react_to_archived_wager(wager)
            except Exception as exc:  # pragma: no cover - defensive
                print(
                    f"Archive reaction: unexpected error for wager {wager.get('id')}: {exc}"
                )

        await asyncio.sleep(interval)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    global _archive_poll_task
    if _archive_poll_task is None or _archive_poll_task.done():
        _archive_poll_task = client.loop.create_task(_archive_reaction_poller())


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

        image_attachments: List[discord.Attachment] = []
        for attachment in message.attachments:
            content_type = (attachment.content_type or "").lower()
            if "image" in content_type or attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                image_attachments.append(attachment)

        if not image_attachments:
            await message.channel.send("❌ I didn't find an image attachment. Please attach a screenshot (PNG/JPG).")
            return

        try:
            user_id = ensure_user_and_get_id(message.author)
            total_images = len(image_attachments)
            status_text = (
                "🧐 Reading your screenshot…"
                if total_images == 1
                else f"🧐 Reading {total_images} screenshots…"
            )
            await message.channel.send(status_text)

            extra_context = parts[1].strip() if len(parts) > 1 else ""
            success_blocks: List[str] = []
            error_blocks: List[str] = []

            for index, attachment in enumerate(image_attachments, start=1):
                try:
                    parsed = parse_wager_from_image(attachment.url, extra_context=extra_context)
                    description = parsed["description"] or "Bet (screenshot)"
                    if parsed.get("is_live_bet") and not description.strip().startswith(LIVE_PREFIX.strip()):
                        description = f"{LIVE_PREFIX}{description}"
                    amount = float(parsed["amount"] or 0)
                    line = parsed["line"] or ""
                    is_free_play = bool(parsed.get("is_free_play"))

                    matchup, matchup_notes = resolve_matchup_ids(parsed)
                    create_wager(
                        user_id=user_id,
                        description=description,
                        amount=amount,
                        line=line,
                        is_free_play=is_free_play,
                        legs=parsed["legs"],
                        matchup=matchup,
                        discord_message_id=str(message.id),
                        discord_channel_id=str(message.channel.id),
                    )

                    leg_lines = "\n".join(
                        f"    - {leg['description']} ({leg['status']})" for leg in parsed["legs"]
                    )
                    block_lines = [
                        f"**Image #{index}: {attachment.filename or 'screenshot'}**",
                        f"• **Desc:** {description}",
                        f"• **Amount:** ${amount:.2f}",
                        f"• **Line:** {line or '(unknown)'}",
                    ]
                    if is_free_play:
                        block_lines.append("• **Type:** Free Play")
                    if leg_lines:
                        block_lines.append("• **Legs:**\n" + leg_lines)
                    if matchup_notes:
                        block_lines.append("• Matchup mapping: " + "; ".join(matchup_notes))
                    success_blocks.append("\n".join(block_lines))

                except requests.HTTPError as http_err:
                    response = http_err.response
                    if response is not None:
                        detail = f"{response.status_code} {response.text[:200]}"
                    else:
                        detail = str(http_err)
                    error_blocks.append(
                        f"Image #{index}: API error while creating the wager — {detail}"
                    )
                except Exception as exc:
                    error_blocks.append(
                        f"Image #{index}: failed to process — {exc}"
                    )

            message_parts: List[str] = []
            if success_blocks:
                header = (
                    "**Tracked!**"
                    if len(success_blocks) == 1
                    else f"**Tracked {len(success_blocks)} wagers!**"
                )
                message_parts.append(header)
                message_parts.append("\n\n".join(success_blocks))
                if WEB_UI_URL:
                    message_parts.append(f"Tracker UI: {WEB_UI_URL}")
            if error_blocks:
                issues = "\n".join(f"• {text}" for text in error_blocks)
                issue_header = "Issues encountered:" if success_blocks else "❌ Unable to process all attachments:"
                message_parts.append(f"{issue_header}\n{issues}")
            final_message = "\n\n".join(part for part in message_parts if part)
            if final_message:
                await message.channel.send(final_message)
            else:
                await message.channel.send(
                    "❌ Sorry, I couldn't process any of those attachments. Try again or post clearer screenshots."
                )

        except requests.HTTPError as http_err:
            response = http_err.response
            if response is not None:
                detail = f"{response.status_code} {response.text[:200]}"
            else:
                detail = str(http_err)
            await message.channel.send(f"❌ API error: {detail}")
        except Exception as exc:
            await message.channel.send(
                f"❌ Sorry, I couldn't process that: `{exc}`. Try again or post clearer screenshots."
            )


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise SystemExit("Missing DISCORD_TOKEN")
    if not API_URL:
        raise SystemExit("Missing API_URL")
    if not OPENAI_API_KEY:
        print("⚠️  Warning: OPENAI_API_KEY not set. !track will fail on parsing.")
    client.run(DISCORD_TOKEN)
