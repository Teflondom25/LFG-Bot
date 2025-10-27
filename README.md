## 🚀 LFG Subscription Bot


### 🎯 Problem Solved: Eliminating LFG Spam

The traditional "Looking for Group" (LFG) system using **Discord reaction roles** often creates massive notifications and spam, forcing users to mute channels or leave roles altogether.

This bot introduces a **smart, targeted subscription model**. Instead of pinging hundreds of people who are subscribed to the game role but aren't currently playing, the bot only notifies users who have **explicitly subscribed** to notifications for that specific game. This ensures pings are relevant and keeps your community channels clean and usable.


### ✨ Core Functionality

The LFG Bot manages persistent, database-backed game subscriptions for every user.



* **Targeted Pinging:** Only subscribed users are pinged for an LFG request.
* **Automatic Thread Creation:** The /lfg command automatically creates a new thread in the channel, centralizing the LFG conversation and preventing main channel disruption.
* **Data Normalization:** All game names are normalized (Deep Rock Galactic -> deep-rock-galactic) to prevent users from creating duplicate entries due to spelling or capitalization errors.
* **Intelligent Autocomplete:** Suggestions are drawn from a comprehensive games.txt file and existing database entries for a seamless user experience.


### 🛠️ Technology Stack


<table>
  <tr>
   <td><strong>Component</strong>
   </td>
   <td><strong>Technology</strong>
   </td>
   <td><strong>Purpose</strong>
   </td>
  </tr>
  <tr>
   <td><strong>Language</strong>
   </td>
   <td>Python 3.10+
   </td>
   <td>Primary development language.
   </td>
  </tr>
  <tr>
   <td><strong>Framework</strong>
   </td>
   <td>discord.py (App Commands)
   </td>
   <td>Handling Discord interactions, slash commands, and events.
   </td>
  </tr>
  <tr>
   <td><strong>Database</strong>
   </td>
   <td>Google Cloud Firestore
   </td>
   <td>Persistent, real-time storage for user subscriptions.
   </td>
  </tr>
  <tr>
   <td><strong>Authentication</strong>
   </td>
   <td>Firebase Admin SDK
   </td>
   <td>Secure, administrative access to Firestore using a service account key.
   </td>
  </tr>
  <tr>
   <td><strong>Configuration</strong>
   </td>
   <td>python-dotenv
   </td>
   <td>Managing sensitive environment variables (.env file).
   </td>
  </tr>
  <tr>
   <td><strong>Concurrency</strong>
   </td>
   <td>asyncio
   </td>
   <td>Ensuring non-blocking database operations to keep the bot highly responsive.
   </td>
  </tr>
</table>



### ⚙️ Setup and Installation


#### Prerequisites



1. A Discord Bot Token and Guild ID.
2. A Google Cloud Project with a Firebase Firestore database initialized.
3. A Firebase Service Account JSON file for secure database access.


#### Environment Configuration

Create a file named .env in the root directory with the following variables:

# Discord Credentials
DISCORD_BOT_TOKEN="YOUR_DISCORD_BOT_TOKEN_HERE" 
DISCORD_GUILD_ID="YOUR_MAIN_SERVER_ID_FOR_COMMAND_SYNC" 
 
# Firebase Credentials
# Path to your downloaded service account key (e.g., ./serviceAccountKey.json)
FIREBASE_SERVICE_ACCOUNT_PATH="./your-service-account-key-name.json"  



#### Running the Bot



1. **Install Dependencies:** 
pip install discord.py firebase-admin python-dotenv aiofiles 

2. **Run the Script:** 
python "LFG Bot.py" 



### 📋 Command Reference


<table>
  <tr>
   <td><strong>Command</strong>
   </td>
   <td><strong>Description</strong>
   </td>
   <td><strong>Example</strong>
   </td>
  </tr>
  <tr>
   <td><strong>/addgame</strong>
   </td>
   <td>Subscribe to notifications for a specific game.
   </td>
   <td>/addgame game: Helldivers 2
   </td>
  </tr>
  <tr>
   <td><strong>/removegame</strong>
   </td>
   <td>Unsubscribe from a game's notification list.
   </td>
   <td>/removegame game: Destiny 2
   </td>
  </tr>
  <tr>
   <td><strong>/lfg</strong>
   </td>
   <td>Ping all subscribers for a game. Starts a new dedicated thread automatically.
   </td>
   <td>/lfg game: Palworld message: Need 2 more for boss fight!
   </td>
  </tr>
  <tr>
   <td><strong>/mygames</strong>
   </td>
   <td>Lists all the games you are currently subscribed to.
   </td>
   <td>/mygames
   </td>
  </tr>
  <tr>
   <td><strong>/listgames</strong>
   </td>
   <td>Shows all games that currently have at least one subscriber in the database.
   </td>
   <td>/listgames
   </td>
  </tr>
  <tr>
   <td><strong>/help</strong>
   </td>
   <td>Displays the bot's functionality and command list.
   </td>
   <td>/help
   </td>
  </tr>
</table>



### 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated!



1. Fork the Project.
2. Create your Feature Branch (git checkout -b feature/AmazingFeature).
3. Commit your Changes (git commit -m 'Add some AmazingFeature').
4. Push to the Branch (git push origin feature/AmazingFeature).
5. Open a Pull Request.
