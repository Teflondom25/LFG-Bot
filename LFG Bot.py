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
from keep_alive import keep_alive # CRITICAL: Import for hosting stability


# Load environment variables (needed if run outside main() which is good practice)
load_dotenv()

# --- Global Firebase Client (initialized later) ---
db = None 

# --- Discord Client and Tree Setup ---
class LFGClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # We need an ApplicationCommandTree for slash commands
        self.tree = app_commands.CommandTree(self)
        self.common_games = []

    async def setup_hook(self):
        target_guild = discord.Object(id=config.GUILD_ID)
        
        # 1. Sync commands to the test guild (for quick development updates)
        self.tree.copy_global_to(guild=target_guild)
        await self.tree.sync(guild=target_guild)
        print(f"Commands synced to test guild: {config.GUILD_ID}")

        # 2. Globally sync commands (so they appear on ALL servers)
        await self.tree.sync()
        print("Commands synced globally. They may take up to an hour to appear on all servers.")

        
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        await self.load_common_games()

    async def load_common_games(self):
        """Loads common game names from games.txt for autocompletion."""
        try:
            # Look for the file in the current working directory
            async with aiofiles.open('games.txt', mode='r') as f:
                content = await f.read()
            self.common_games = [line.strip().lower() for line in content.splitlines() if line.strip()]
            print(f"Loaded {len(self.common_games)} common games for autocompletion.")
        except FileNotFoundError:
            print("Warning: games.txt not found. Autocompletion suggestions will be limited to existing database entries.")
        except Exception as e:
            print(f"Error loading games.txt: {e}")

# Initialize client with intents from config
client = LFGClient(intents=config.INTENTS)


# --- Firebase & Bot Initialization ---

def initialize_services():
    """
    Initializes Firebase Admin.
    Prioritizes reading key content from the FIREBASE_KEY_CONTENT env var (for cloud deployment),
    but falls back to loading the file directly from the path (for local development).
    """
    global db
    try:
        key_path = config.FIREBASE_SERVICE_ACCOUNT_PATH
        key_content_json = os.getenv('FIREBASE_KEY_CONTENT')
        source_message = ""
        cleanup_temp_file = False

        if key_content_json:
            # 1. Cloud Deployment Path (e.g., Railway/Replit)
            # Write the JSON content from the environment variable to a temporary file
            with open(key_path, 'w') as f:
                f.write(key_content_json)
            source_message = "Key loaded from FIREBASE_KEY_CONTENT environment variable (Cloud mode)."
            cleanup_temp_file = True
        elif os.path.exists(key_path):
             # 2. Local Development Path (e.g., PyCharm/Local PC)
            # Check if the file exists at the specified path
            source_message = f"Key loaded directly from local file: {key_path} (Local mode)."
        else:
            print("--- FIREBASE KEY MISSING ---")
            print("ERROR: FIREBASE_KEY_CONTENT environment variable not set, AND local file 'serviceAccountKey.json' not found.")
            return False

        # If a source was found, initialize Firebase
        if key_content_json or os.path.exists(key_path):
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized.")
            print(source_message)

            # Get the Firestore client
            db = firestore.client()
            print("Firestore client obtained.")

            # Clean up the temporary file if running in cloud mode
            if cleanup_temp_file:
                os.remove(key_path)
                print(f"Temporary file '{key_path}' removed.")
            return True
        
        return False

    except Exception as e:
        print(f"Firebase initialization failed: {e}\n{traceback.format_exc()}")
        return False

# --- Firestore Path Helpers (Multi-Server Logic) ---

def get_guild_collection_path(guild_id: int) -> str:
    """
    Constructs the base collection path for a specific guild.
    Path must be an odd number of elements (Collection/Document/Collection).
    Example: lfg_data/123456789/games
    """
    # config.get_lfg_collection_path() returns "lfg_data"
    # This is COLLECTION/DOCUMENT/COLLECTION
    return f"{config.get_lfg_collection_path()}/{guild_id}/games"


def get_game_doc_path(guild_id: int, game_name: str) -> str:
    """
    Constructs the document path for a specific game within a specific guild.
    Path must be an even number of elements (Collection/Document/Collection/Document).
    Example: lfg_data/123456789/games/destiny-2
    """
    # This is COLLECTION/DOCUMENT/COLLECTION/DOCUMENT
    return f"{get_guild_collection_path(guild_id)}/{game_name}"

# --- Firestore Synchronization Functions (Run in executor) ---

def add_subscription_sync(doc_path: str, user_id: int):
    """Adds a user ID to the 'subscribers' array for a specific game document."""
    game_doc_ref = db.document(doc_path)
    # The update function is atomic and safe for concurrent use.
    # It creates the document if it doesn't exist (using set with merge=True).
    game_doc_ref.set(
        {'subscribers': firestore.ArrayUnion([user_id])},
        merge=True
    )


def remove_subscription_sync(doc_path: str, user_id: int):
    """Removes a user ID from the 'subscribers' array for a specific game document."""
    game_doc_ref = db.document(doc_path)
    game_doc_ref.update({
        'subscribers': firestore.ArrayRemove([user_id])
    })

def get_all_subscribed_games_sync(guild_id: int) -> list:
    """Retrieves all games with subscribers for a specific guild."""
    guild_collection_path = get_guild_collection_path(guild_id)
    
    # We use a CollectionReference stream to iterate over documents in the guild's 'games' collection.
    docs_stream = db.collection(guild_collection_path).stream()
    
    # Process the stream to build a list of games and their subscriber counts
    all_games_data = []
    for doc in docs_stream:
        data = doc.to_dict()
        subscribers = data.get('subscribers', [])
        
        # Only include games that have at least one subscriber
        if subscribers:
            all_games_data.append({
                'name': doc.id,
                'count': len(subscribers)
            })
            
    return all_games_data

def get_user_subscribed_games_sync(guild_id: int, user_id: int) -> list:
    """Retrieves all games a specific user is subscribed to in a specific guild."""
    guild_collection_path = get_guild_collection_path(guild_id)
    
    # Query for documents in the guild's 'games' collection where the 'subscribers' array contains the user's ID
    query = db.collection(guild_collection_path).where('subscribers', 'array_contains', user_id)
    docs = query.stream()
    
    # Return a list of game names (document IDs)
    return [doc.id for doc in docs]


def get_game_subscribers_sync(doc_path: str) -> list:
    """Retrieves the list of subscribers for a single game document."""
    doc_ref = db.document(doc_path)
    doc_snapshot = doc_ref.get()
    if doc_snapshot.exists:
        data = doc_snapshot.to_dict()
        return data.get('subscribers', [])
    return []

def get_game_names_sync(guild_id: int) -> list:
    """Retrieves all game names (document IDs) in the guild's collection."""
    guild_collection_path = get_guild_collection_path(guild_id)
    docs_stream = db.collection(guild_collection_path).stream()
    return [doc.id for doc in docs_stream]


# --- Autocomplete Logic ---

async def game_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """Provides game suggestions for slash commands."""
    try:
        guild_id = interaction.guild_id
        if not guild_id:
            # Cannot autocomplete if not in a guild context
            return [] 
        
        # 1. Get existing games from Firestore (synchronous operation run in thread)
        existing_games = await asyncio.to_thread(get_game_names_sync, guild_id)
        
        # 2. Combine with common games list and ensure uniqueness
        all_games = set(client.common_games + [g.lower() for g in existing_games])
        
        # 3. Filter and format the choices
        choices = []
        current_lower = current.lower()
        
        for game in all_games:
            if current_lower in game:
                # Limit to 25 choices as per Discord API limit
                if len(choices) < 25: 
                    # Display the name with Title Case but ensure the returned value is lowercase/normalized
                    display_name = game.replace('-', ' ').title()
                    choices.append(app_commands.Choice(name=display_name, value=game))

        return choices

    except Exception as e:
        print(f"Error in autocomplete: {e}")
        # Return empty list on failure
        return []

# --- Discord Slash Commands ---

@client.tree.command(name="addgame", description="Subscribe to notifications for a specific game.")
@app_commands.describe(game="The name of the game you want to follow (e.g., Destiny 2)")
@app_commands.autocomplete(game=game_autocomplete)
async def addgame(interaction: discord.Interaction, game: str):
    try:
        if not interaction.guild_id:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        # 1. Normalize and get paths
        normalized_game = game.lower().replace(' ', '-')
        doc_path = get_game_doc_path(interaction.guild_id, normalized_game)
        user_id = interaction.user.id
        
        # 2. Run sync function in a thread
        await asyncio.to_thread(add_subscription_sync, doc_path, user_id)

        await interaction.response.send_message(
            f"You are now subscribed to LFG notifications for **{game}**!", 
            ephemeral=True
        )

    except Exception as e:
        print(f"Error in /addgame: {e}\n{traceback.format_exc()}")
        await interaction.response.send_message("An error occurred while adding your game subscription.", ephemeral=True)


@client.tree.command(name="removegame", description="Unsubscribe from notifications for a specific game.")
@app_commands.describe(game="The name of the game you want to unfollow")
@app_commands.autocomplete(game=game_autocomplete)
async def removegame(interaction: discord.Interaction, game: str):
    try:
        if not interaction.guild_id:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        # 1. Normalize and get path
        normalized_game = game.lower().replace(' ', '-')
        doc_path = get_game_doc_path(interaction.guild_id, normalized_game)
        user_id = interaction.user.id
        
        # 2. Run sync function in a thread
        await asyncio.to_thread(remove_subscription_sync, doc_path, user_id)

        await interaction.response.send_message(
            f"You have been unsubscribed from **{game}**.", 
            ephemeral=True
        )

    except Exception as e:
        print(f"Error in /removegame: {e}\n{traceback.format_exc()}")
        await interaction.response.send_message("An error occurred while removing your game subscription.", ephemeral=True)


@client.tree.command(name="lfg", description="Ping all subscribers for a specific game to start a group.")
@app_commands.describe(
    game="The name of the game you want to play",
    message="An optional message for your LFG (e.g., 'Need 2 more')"
)
@app_commands.autocomplete(game=game_autocomplete)
async def lfg(interaction: discord.Interaction, game: str, message: str = "Anyone want to play?"):
    await interaction.response.defer() # Defer the public reply

    try:
        if not interaction.guild_id:
            await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
            return

        # 1. Normalize and get path
        normalized_game = game.lower().replace(' ', '-')
        doc_path = get_game_doc_path(interaction.guild_id, normalized_game)
        user_id = interaction.user.id

        # 2. Get the subscribers (synchronous operation run in thread)
        subscribers = await asyncio.to_thread(get_game_subscribers_sync, doc_path)

        if not subscribers:
            await interaction.followup.send(
                f"Sorry, no one is subscribed to **{game}** yet in this server. Be the first with `/addgame`!",
                ephemeral=True
            )
            return

        # 3. Filter out the person who started the LFG and create ping string
        users_to_ping = [f"<@{id}>" for id in subscribers if id != user_id]
        
        ping_string = " ".join(users_to_ping)
        if not ping_string:
            ping_string = "You are the only subscriber currently!"

        # 4. Create a thread for the LFG conversation
        thread = await interaction.channel.create_thread(
            name=f"LFG: {game} ({interaction.user.display_name})",
            auto_archive_duration=60,  # 1 hour
            reason=f"LFG started by {interaction.user.display_name} for {game}",
        )
        
        # 5. Send the ping message inside the thread
        await thread.send(
            f"**LFG for {game.title()}!**\n"
            f"*Started by {interaction.user.mention}*\n\n"
            f"> {message}\n\n"
            f"{'Pinging subscribers:' if users_to_ping else 'No one else to ping.'} {ping_string}"
        )

        # 6. Reply in the main channel linking to the thread
        await interaction.followup.send(
            f"LFG for **{game}** started! Join the conversation in the thread: {thread.mention}"
        )

    except Exception as e:
        print(f"Error in /lfg: {e}\n{traceback.format_exc()}")
        await interaction.followup.send("An error occurred while creating the LFG post.", ephemeral=True)


@client.tree.command(name="mygames", description="List all the games you are currently subscribed to.")
@app_commands.guild_only()
async def mygames(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    try:
        # Run sync function in a thread
        user_id = interaction.user.id
        guild_id = interaction.guild_id
        my_games = await asyncio.to_thread(get_user_subscribed_games_sync, guild_id, user_id)

        if not my_games:
            await interaction.followup.send('You are not subscribed to any games yet. Use `/addgame` to subscribe!')
        else:
            # Format game names for display
            game_list = [f"- **{game.replace('-', ' ').title()}**" for game in my_games]
            await interaction.followup.send(
                f"You are subscribed to the following games in this server:\n{'\n'.join(game_list)}"
            )

    except Exception as e:
        print(f"Error in /mygames: {e}\n{traceback.format_exc()}")
        await interaction.followup.send("An error occurred while fetching your subscriptions.", ephemeral=True)


@client.tree.command(name="listgames", description="List all games that have at least one subscriber in this server.")
@app_commands.guild_only()
async def listgames(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    try:
        guild_id = interaction.guild_id
        # Run sync function in a thread
        all_games = await asyncio.to_thread(get_all_subscribed_games_sync, guild_id)

        if not all_games:
            await interaction.followup.send('There are no games with subscribers in this server yet.')
        else:
            # Sort by most popular (descending)
            all_games.sort(key=lambda x: x['count'], reverse=True)
            
            game_list = []
            for game in all_games:
                name = game['name'].replace('-', ' ').title()
                count = game['count']
                game_list.append(f"- **{name}** ({count} {('subscriber', 'subscribers')[count != 1]})")

            await interaction.followup.send(
                f"Here are the current games with subscribers in this server:\n{'\n'.join(game_list)}"
            )

    except Exception as e:
        print(f"Error in /listgames: {e}\n{traceback.format_exc()}")
        await interaction.followup.send("An error occurred while fetching the game list.", ephemeral=True)


# --- Start the Bot ---

def main():
    """The main entry point for the bot."""
    # Initialize Firebase first
    firebase_initialized = initialize_services()

    # Consolidated check for cloud deployment 
    if not firebase_initialized or not all([config.DISCORD_BOT_TOKEN, config.GUILD_ID, db]):
        print("--- CONFIGURATION ERROR ---")
        print("The Firebase client failed to initialize or environment variables are missing.")
        print("Please ensure DISCORD_BOT_TOKEN, GUILD_ID, and FIREBASE_KEY_CONTENT are set in your cloud platform.")
        sys.exit(1)

    try:
        print("Attempting to log in to Discord...")
        # CRITICAL: Start the web server to keep the bot alive on cloud platforms
        keep_alive() 
        client.run(config.DISCORD_BOT_TOKEN)

    except discord.LoginFailure:
        print("--- LOGIN FAILURE ---")
        print("Error: Failed to log in. The DISCORD_BOT_TOKEN is incorrect.")
        sys.exit(1)

    except Exception as e:
        print(f"--- AN UNEXPECTED ERROR OCCURRED ---")
        print(f"Error: {e}\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == '__main__':
    main()
