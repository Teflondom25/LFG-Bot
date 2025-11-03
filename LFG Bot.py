import os
import discord
from discord import app_commands
import firebase_admin
from firebase_admin import credentials, firestore
import config
import sys
import traceback
import aiofiles
import asyncio
from dotenv import load_dotenv
from keep_alive import keep_alive


# --- Firebase & Bot Initialization ---

def initialize_services():
    """Initializes Firebase Admin. Handles key content from Railway environment variables."""
    try:
        # 1. Read the key content from the environment variable set in Railway
        key_content_json = os.getenv('FIREBASE_KEY_CONTENT')

        if not key_content_json:
            print("--- FIREBASE KEY MISSING ---")
            print("ERROR: FIREBASE_KEY_CONTENT environment variable not set.")
            return None

        # 2. Temporarily write the JSON content to a file (required by credentials.Certificate)
        # config.FIREBASE_SERVICE_ACCOUNT_PATH should be set to 'serviceAccountKey.json'
        key_path = config.FIREBASE_SERVICE_ACCOUNT_PATH
        with open(key_path, 'w') as f:
            f.write(key_content_json)

        # 3. Initialize Firebase using the temporary file path
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized.")

        # 4. Get the Firestore client
        db = firestore.client()
        print("Firestore client obtained.")

        # 5. Clean up the temporary file immediately after initialization
        os.remove(key_path)
        print(f"Temporary file '{key_path}' removed.")

        return db

    except Exception as e:
        print(f"--- FIREBASE UNEXPECTED ERROR ---")
        print(f"An unexpected error occurred during Firebase init: {e}")
        print("---------------------------------")
        return None

# Initialize Firestore
db = initialize_services()

# Get the collection path from our config
LFG_COLLECTION = config.get_lfg_collection_path()


# Define a helper to normalize game names
def normalize_game_name(name: str) -> str:
    """Converts game name to a consistent format for the database."""
    return name.lower().strip().replace(' ', '-')


# --- Global Game List for Autocomplete ---
COMMON_GAMES = []


async def load_common_games():
    """Loads the list of common games from games.txt for autocompletion."""
    try:
        async with aiofiles.open('games.txt', mode='r') as f:
            content = await f.read()
            global COMMON_GAMES
            COMMON_GAMES = [line.strip().lower() for line in content.splitlines() if line.strip()]
        print(f"Loaded {len(COMMON_GAMES)} common games for autocompletion.")
    except FileNotFoundError:
        print("Warning: games.txt not found. Autocompletion will only suggest existing database entries.")
    except Exception as e:
        print(f"Error loading games.txt: {e}")


# --- Bot Client Setup ---

class LfgBotClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        """This is called when the bot logs in, to sync commands and load data."""
        await load_common_games()

        if config.GUILD_ID:
            self.tree.copy_global_to(guild=config.GUILD_ID)
            await self.tree.sync(guild=config.GUILD_ID)
            print(f"Synced commands to guild: {config.GUILD_ID.id}")
        else:
            print("Error: GUILD_ID not set in .env file. Commands will not be synced.")


client = LfgBotClient(intents=config.INTENTS)


# --- Bot Event Listeners ---

@client.event
async def on_ready():
    """Called when the bot is connected and ready."""
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')


# --- Autocompletion Function ---

async def game_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """Provides suggestions for game names based on common games and existing database entries."""

    # Run synchronous database query in a separate thread
    def fetch_db_games():
        if db:
            return [doc.id for doc in db.collection(LFG_COLLECTION).stream()]
        return []

    # Wait for the database results
    db_games = await asyncio.to_thread(fetch_db_games)

    # Combine and normalize the full list of suggestions
    readable_db_games = [g.replace('-', ' ').title() for g in db_games]
    suggestions = set(COMMON_GAMES + readable_db_games)

    # Filter suggestions based on what the user is typing (current)
    filtered_suggestions = [
        s for s in suggestions
        if current.lower() in s.lower()
    ]

    # Limit to Discord's maximum of 25 choices
    return [
        app_commands.Choice(name=name.title(), value=name.title())
        for name in filtered_suggestions[:25]
    ]


# --- Firestore Synchronous Helper Functions ---

def add_subscription_sync(game_name: str, user_id: str):
    """Synchronous function to add a user to a game's subscription list."""
    game_doc_ref = db.collection(LFG_COLLECTION).document(game_name)
    game_doc_ref.set({
        'subscribers': firestore.ArrayUnion([user_id])
    }, merge=True)


def remove_subscription_sync(game_name: str, user_id: str):
    """Synchronous function to remove a user from a game's subscription list."""
    game_doc_ref = db.collection(LFG_COLLECTION).document(game_name)
    game_doc_ref.update({
        'subscribers': firestore.ArrayRemove([user_id])
    })


def get_game_subscribers_sync(game_name: str):
    """Synchronous function to retrieve a game document snapshot."""
    game_doc_ref = db.collection(LFG_COLLECTION).document(game_name)
    return game_doc_ref.get()


# Helper function to execute synchronous database stream logic
def get_user_subscriptions_sync(user_id):
    """Synchronously queries Firestore for games a user is subscribed to."""
    query = db.collection(LFG_COLLECTION).where('subscribers', 'array_contains', user_id)
    return [doc.id for doc in query.stream()]


# Helper function to execute synchronous database stream logic
def get_all_subscribed_games_sync():
    """Synchronously queries Firestore for all games with subscribers."""
    docs_stream = db.collection(LFG_COLLECTION).stream()
    all_games = []

    for doc in docs_stream:
        data = doc.to_dict()
        subscribers = data.get('subscribers', [])
        if subscribers:  # Only list if it has subscribers
            all_games.append({'name': doc.id, 'count': len(subscribers)})
    return all_games


# --- Bot Command Definitions ---

@client.tree.command(name="help", description="Explains the bot's function and lists all commands.")
async def help_command(interaction: discord.Interaction):
    """Command to show the help menu."""
    await interaction.response.defer(ephemeral=True)

    help_message = """
**🚀 LFG SUBSCRIPTION BOT HELP**
---
This bot replaces traditional reaction roles with a smart, targeted subscription system. When you use `/lfg`, the bot only pings users who have **explicitly subscribed** to that game, preventing massive role spam!

**✅ Key Feature: Preventing Duplicates**
All game names are automatically converted to a standardized format (e.g., "Deep Rock Galactic" -> `deep-rock-galactic`), so misspellings or casing issues won't create multiple entries.

**COMMANDS LIST:**
---
**1. Subscribing/Unsubscribing**
- **`/addgame game: [Name]`**: Subscribe to a game's notification list.
- **`/removegame game: [Name]`**: Unsubscribe from a game.

**2. Looking For Group (LFG)**
- **`/lfg game: [Name] message: [Optional]`**: Ping all subscribers for that game. A **new thread** is automatically created to keep the main channel clean!

**3. Checking Status**
- **`/mygames`**: Lists all games you are personally subscribed to.
- **`/listgames`**: Shows all games in the server that currently have subscribers.
- **`/help`**: Displays this help message.
"""

    await interaction.followup.send(help_message, ephemeral=True)


@client.tree.command(name="addgame", description="Subscribe to notifications for a specific game.")
@app_commands.autocomplete(game=game_autocomplete)
@app_commands.describe(game="The name of the game you want to follow (e.g., Helldivers 2)")
async def addgame(interaction: discord.Interaction, game: str):
    """Command to add a game subscription."""
    if not db:
        await interaction.response.send_message("Error: Database is not connected.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    game_name = normalize_game_name(game)
    user_id = str(interaction.user.id)

    try:
        # FIX: Offload synchronous write to a separate thread
        await asyncio.to_thread(add_subscription_sync, game_name, user_id)

        await interaction.followup.send(f"You are now subscribed to notifications for **{game_name}**!")
    except Exception as e:
        print(f"Error in /addgame: {e}\n{traceback.format_exc()}")
        await interaction.followup.send("An error occurred while subscribing.", ephemeral=True)


@client.tree.command(name="removegame", description="Unsubscribe from notifications for a specific game.")
@app_commands.autocomplete(game=game_autocomplete)
@app_commands.describe(game="The name of the game you want to unfollow")
async def removegame(interaction: discord.Interaction, game: str):
    """Command to remove a game subscription."""
    if not db:
        await interaction.response.send_message("Error: Database is not connected.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    game_name = normalize_game_name(game)
    user_id = str(interaction.user.id)

    try:
        # FIX: Offload synchronous write to a separate thread
        await asyncio.to_thread(remove_subscription_sync, game_name, user_id)

        await interaction.followup.send(f"You have been unsubscribed from **{game_name}**.")
    except Exception as e:
        print(f"Info: /removegame error (might be benign): {e}")
        await interaction.followup.send(f"You are no longer subscribed to **{game_name}** (if you were).",
                                        ephemeral=True)


@client.tree.command(name="lfg", description="Ping all subscribers for a specific game to start a group.")
@app_commands.autocomplete(game=game_autocomplete)
@app_commands.describe(
    game="The name of the game you want to play",
    message="An optional message for your LFG (e.g., 'Need 2 more')"
)
async def lfg(interaction: discord.Interaction, game: str, message: str = None):
    """Command to start an LFG and ping subscribers."""
    if not db:
        await interaction.response.send_message("Error: Database is not connected.", ephemeral=True)
        return

    await interaction.response.defer()  # Public reply
    game_name = normalize_game_name(game)
    lfg_message = message or "Anyone want to play?"
    user_id = str(interaction.user.id)

    try:
        # FIX: Offload synchronous read to a separate thread
        doc_snap = await asyncio.to_thread(get_game_subscribers_sync, game_name)

        if not doc_snap.exists:
            await interaction.followup.send(
                f"Sorry, no one is subscribed to **{game_name}** yet. Be the first with `/addgame`!")
            return

        data = doc_snap.to_dict()
        subscribers = data.get('subscribers', [])

        if not subscribers:
            await interaction.followup.send(f"Sorry, no one is subscribed to **{game_name}** yet.")
            return

        # Filter out the person who started the LFG
        users_to_ping = [sub_id for sub_id in subscribers if sub_id != user_id]
        ping_string = ' '.join([f'<@{sub_id}>' for sub_id in users_to_ping])

        # Best Practice: Create a thread
        thread_starter_message = await interaction.followup.send(f"LFG for **{game_name}** started! Join the thread...")

        thread = await interaction.channel.create_thread(
            name=f"LFG for {game_name} ({interaction.created_at.strftime('%H:%M')})",
            message=thread_starter_message
        )

        # Now send the real LFG message inside the thread
        await thread.send(f"""
**LFG for {game_name}!**
*Started by {interaction.user.mention}*

> {lfg_message}

{f'Pinging subscribers: {ping_string}' if ping_string else 'Pinging subscribers... (no one else subscribed)'}
        """)

    except Exception as e:
        print(f"Error in /lfg: {e}\n{traceback.format_exc()}")
        await interaction.followup.send("An error occurred while starting the LFG.", ephemeral=True)


@client.tree.command(name="mygames", description="List all the games you are currently subscribed to.")
async def mygames(interaction: discord.Interaction):
    """Command to list the user's current game subscriptions."""
    if not db:
        await interaction.response.send_message("Error: Database is not connected.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    user_id = str(interaction.user.id)

    try:
        # Use asyncio.to_thread to run the synchronous database query
        my_games = await asyncio.to_thread(get_user_subscriptions_sync, user_id)

        if not my_games:
            await interaction.followup.send("You are not subscribed to any games yet. Use `/addgame` to subscribe!")
        else:
            game_list = '\n- '.join(my_games)
            await interaction.followup.send(f"You are subscribed to:\n- {game_list}")

    except Exception as e:
        print(f"Error in /mygames: {e}\n{traceback.format_exc()}")
        await interaction.followup.send("An error occurred while fetching your games.", ephemeral=True)


@client.tree.command(name="listgames", description="List all games that have at least one subscriber.")
async def listgames(interaction: discord.Interaction):
    """Command to list all available games with subscribers."""
    if not db:
        await interaction.response.send_message("Error: Database is not connected.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    try:
        # Use asyncio.to_thread to run the synchronous database query
        all_games = await asyncio.to_thread(get_all_subscribed_games_sync)

        if not all_games:
            await interaction.followup.send("There are no games with subscribers yet.")
        else:
            # Sort by most popular
            all_games.sort(key=lambda g: g['count'], reverse=True)
            game_list = '\n'.join([
                f"- **{game['name']}** ({game['count']} {'subscriber' if game['count'] == 1 else 'subscribers'})"
                for game in all_games
            ])
            await interaction.followup.send(f"Here are the current games with subscribers:\n{game_list}")

    except Exception as e:
        print(f"Error in /listgames: {e}\n{traceback.format_exc()}")
        await interaction.followup.send("An error occurred while fetching the game list.", ephemeral=True)


# --- Start the Bot ---

def main():
    """The main entry point for the bot."""
    load_dotenv() # Load variables from .env file

    if not all([config.DISCORD_BOT_TOKEN, config.GUILD_ID, config.FIREBASE_SERVICE_ACCOUNT_PATH, db]):
        print("--- CONFIGURATION ERROR ---")
        print(f"DISCORD_BOT_TOKEN: {'SET' if config.DISCORD_BOT_TOKEN else 'MISSING'}")
        print(f"GUILD_ID: {'SET' if config.GUILD_ID else 'MISSING'}")
        print(f"FIREBASE_SERVICE_ACCOUNT_PATH: {'SET' if config.FIREBASE_SERVICE_ACCOUNT_PATH else 'MISSING'}")
        print(f"Firebase DB Client: {'SET' if db else 'MISSING'}")
        print("---------------------------")
        sys.exit(1)

    try:
        print("Attempting to log in to Discord...")
        keep_alive() # Start web server thread for UptimeRobot
        client.run(config.DISCORD_BOT_TOKEN)

    except discord.LoginFailure:
        print("--- LOGIN FAILURE ---")
        print("Error: Failed to log in. The DISCORD_BOT_TOKEN is incorrect.")
        print("Please reset your token in the Discord Developer Portal and update your .env file.")
        print("---------------------")
        sys.exit(1)

    except Exception as e:
        print(f"--- AN UNEXPECTED ERROR OCCURRED ---")
        print(f"Error: {e}")
        print(traceback.format_exc())
        print("--------------------------------------")
        sys.exit(1)


if __name__ == "__main__":
    main()
