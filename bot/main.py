import os
import discord
import requests

TOKEN = os.getenv("DISCORD_TOKEN")
API_URL = os.getenv("API_URL", "http://localhost:8000")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Example command: !addwager user_id description amount line
    if message.content.startswith("!addwager"):
        try:
            _, user_id, description, amount, line = message.content.split(maxsplit=4)
            data = {
                "user_id": int(user_id),
                "description": description,
                "amount": float(amount),
                "line": line
            }
            response = requests.post(f"{API_URL}/wagers", json=data)
            if response.status_code == 200:
                await message.channel.send(f"✅ Wager added for user {user_id}")
            else:
                await message.channel.send(f"❌ Failed to add wager: {response.text}")
        except Exception as e:
            await message.channel.send(f"Error parsing wager: {e}")
