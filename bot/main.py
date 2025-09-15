import os
import json
import discord
import requests

# --- Config ---
API_URL = os.getenv("API_URL", "http://web:8000")  # in docker, web:8000 ; locally: http://localhost:8000
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "lv-raiders")

# --- OpenAI (Responses API) ---
# Using the official OpenAI Python SDK (>=1.0). If you prefer, you can keep using requests.
try:
    from openai import OpenAI
    _openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
    print ("OpenAI client initialized.")
except Exception:
    _openai_client = None

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


def _user_payload_from_discord(author: discord.User | discord.Member) -> dict:
    # discord_id must be string to match your API
    discord_id = str(author.id)
    display_name = getattr(author, "display_name", author.name)
    avatar_url = str(author.display_avatar.url) if author.display_avatar else None
    return {
        "discord_id": discord_id,
        "display_name": display_name,
        "profile_pic_url": avatar_url
    }


def ensure_user_and_get_id(author: discord.User | discord.Member) -> int:
    """Create the user if not exists, otherwise fetch their id."""
    payload = _user_payload_from_discord(author)
    # Try to create
    r = requests.post(f"{API_URL}/users/", json=payload, timeout=10)
    if r.status_code == 200:
        return r.json()["id"]
    # If exists, your API returns 400; fall back to listing + find by discord_id
    if r.status_code == 400:
        r2 = requests.get(f"{API_URL}/users/", timeout=10)
        r2.raise_for_status()
        for u in r2.json():
            if u["discord_id"] == payload["discord_id"]:
                return u["id"]
    # Anything else is unexpected
    r.raise_for_status()
    raise RuntimeError("Failed to ensure user exists")


def parse_wager_from_image(image_url: str) -> dict:
    """
    Ask OpenAI to extract {description, amount, line} from a screenshot.
    If a value is missing, we default amount=0, line="" in the caller.
    """
    if _openai_client is None:
        raise RuntimeError("OpenAI client not initialized. Set OPENAI_API_KEY.")

    system_prompt = (
        "You extract sports bet details from screenshots of sports wagers. "
        "Return STRICT JSON with keys: description (string), amount (number), line (string). "
        "- For parlays: description MUST include all legs in a readable format. "
        "Example: \"3 leg parlay - Vikings -3, Cowboys ML, Bears +7\". "
        "- For player props: include the player name, stat, and threshold. "
        "Example: \"Lamar Jackson over 45.5 rushing yards, Josh Allen over 34.5 rushing yards\". "
        "- For parlays that include player props: merge everything into one description. "
        "Example: \"2 leg parlay - Lamar Jackson over 45.5 rushing yards, Josh Allen over 34.5 rushing yards\". "
        "- Amount must be the stake wagered (the 'Risk'). "
        "- For parlays: if only 'Risk' and 'To Win' are shown, calculate the implied American odds. "
        "Formula: If Win >= Risk → line = +(Win / Risk * 100). "
        "If Win < Risk → line = -(Risk / Win * 100). Round to nearest 5 or 10. "
        "- If a field is unknown, use an empty string for line and 0 for amount. "
        "Do not include any extra keys or text."
    )

    # Responses API: text + image input
    # Ref: OpenAI Responses API docs (image inputs & text outputs)
    resp = _openai_client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": system_prompt},
                    {"type": "input_image", "image_url": image_url},
                ],
            }
        ],
    )

    # Convenient helper on SDK to get all text output
    text = getattr(resp, "output_text", None)
    if not text:
        # Fallback: try to reconstruct from content items
        try:
            parts = []
            for item in resp.output[0].content:
                if item["type"] == "output_text":
                    parts.append(item["text"])
            text = "\n".join(parts)
        except Exception:
            text = ""

    # Parse JSON (model instructed to return strict JSON)
    try:
        data = json.loads(text)
    except Exception:
        # If the model returned something not strictly JSON, try to salvage by locating a JSON block
        import re
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise RuntimeError(f"Model did not return JSON. Raw text:\n{text}")
        data = json.loads(match.group(0))

    # Basic normalization
    desc = str(data.get("description") or "").strip()
    line = str(data.get("line") or "").strip()
    try:
        amount = float(data.get("amount") or 0)
    except Exception:
        amount = 0.0

    return {"description": desc, "amount": amount, "line": line}


def create_wager(user_id: int, description: str, amount: float, line: str) -> dict:
    payload = {
        "user_id": user_id,
        "description": description,
        "amount": amount,
        "line": line
    }
    r = requests.post(f"{API_URL}/wagers/", json=payload, timeout=10)
    r.raise_for_status()
    return r.json()


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    # Ignore self
    if message.author == client.user:
        return

    # Only in #lv-raiders (or env override)
    if isinstance(message.channel, (discord.TextChannel, discord.Thread)) and getattr(message.channel, "name", "") != TARGET_CHANNEL:
        return

    # Command: !track (must include image)
    if message.content.strip().lower().startswith("!track"):
        # Require an attachment that is an image
        if not message.attachments:
            await message.channel.send("❌ Please attach a **screenshot** of the bet with the `!track` command.")
            return

        img = None
        for att in message.attachments:
            # content_type can be None sometimes; also check file extension
            ct = (att.content_type or "").lower()
            if ("image" in ct) or att.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                img = att
                break

        if not img:
            await message.channel.send("❌ I didn't find an image attachment. Please attach a screenshot (PNG/JPG).")
            return

        try:
            # 1) Ensure user exists
            user_id = ensure_user_and_get_id(message.author)

            await message.channel.send("🧐 Reading your screenshot…")

            # 2) Parse wager via OpenAI Vision
            parsed = parse_wager_from_image(img.url)
            desc = parsed["description"] or "Bet (screenshot)"
            amount = float(parsed["amount"] or 0)
            line = parsed["line"] or ""

            # 3) Create wager in your API
            created = create_wager(user_id=user_id, description=desc, amount=amount, line=line)

            # 4) Ack
            summary = f"**Tracked!**\n• **Desc:** {desc}\n• **Amount:** ${amount:.2f}\n• **Line:** {line or '(unknown)'}"
            await message.channel.send(summary)

        except requests.HTTPError as http_err:
            await message.channel.send(f"❌ API error: {http_err.response.status_code} {http_err.response.text}")
        except Exception as e:
            await message.channel.send(f"❌ Sorry, I couldn't process that: `{e}`. Try again or post a clearer screenshot.")


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise SystemExit("Missing DISCORD_TOKEN")
    if not API_URL:
        raise SystemExit("Missing API_URL")
    if not OPENAI_API_KEY:
        print("⚠️  Warning: OPENAI_API_KEY not set. !track will fail on parsing.")
    client.run(DISCORD_TOKEN)
