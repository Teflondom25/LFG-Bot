import os
from dotenv import load_dotenv
import discord

# Load environment variables from .env file
load_dotenv()

# --- Discord Config ---

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# We need to convert the GUILD_ID from a string to a discord.Object
# This is required for the command tree to know which guild to sync to.
GUILD_ID_STR = os.getenv("GUILD_ID")
GUILD_ID = discord.Object(id=GUILD_ID_STR) if GUILD_ID_STR else None

# Define the permissions (intents) the bot needs
# We just need the default intents (like guilds)
INTENTS = discord.Intents.default()

# --- Firebase Config ---
FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")

# Define the Firestore collection path while following Firestore's Collection path rules
LFG_COLLECTION_PATH = 'lfg_subscriptions'

# --- PATH HELPER FUNCTION ---
def get_lfg_collection_path():
    """
    Returns the collection path for storing LFG game subscriptions.
    This function is called by bot.py to retrieve the correct path.
    """
    return LFG_COLLECTION_PATH
