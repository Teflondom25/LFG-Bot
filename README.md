# 🚀 LFG Subscription Bot


## 🎯 Problem Solved: Eliminating LFG Spam

The traditional "Looking for Group" (LFG) system using **Discord reaction roles** often creates massive notifications and spam, forcing users to mute channels or leave roles altogether.

This bot introduces a **smart, targeted subscription model**. Instead of pinging hundreds of people who are subscribed to the game role but aren't currently playing, the bot only notifies users who have **explicitly subscribed** to notifications for that specific game, and crucially, it **sandboxes data by server (Guild)**. This ensures pings are relevant and keeps your community channels clean and usable.


## ✨ Core Functionality

The LFG Bot manages persistent, database-backed game subscriptions for every user on a per-server basis.



* **Targeted Pinging:** Only subscribed users in the requesting server are pinged for an LFG request.


* **Multi-Server Support:** All subscriptions are stored under a unique **Guild ID**, preventing cross-server contamination of LFG pings and data.


* **Automatic Thread Creation:** The /lfg command automatically creates a new thread in the channel, centralizing the LFG conversation and preventing main channel disruption.


* **Data Normalization:** All game names are normalized (Deep Rock Galactic -> deep-rock-galactic) to prevent users from creating duplicate entries due to spelling or capitalization errors.


* **Intelligent Autocomplete:** Suggestions are drawn from a comprehensive games.txt file and existing database entries for a seamless user experience.


## 🛠️ Technology Stack


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
   <td><strong>Concurrency</strong>
   </td>
   <td>asyncio
   </td>
   <td>Ensuring non-blocking database operations to keep the bot highly responsive.
   </td>
  </tr>
</table>



## ⚙️ Setup and Deployment (Cloud Ready)


### Prerequisites



1. A Discord Bot Token
2. A Google Cloud Project with a Firebase Firestore database initialized.
3. A Firebase Service Account JSON file


### Environment Configuration

For deployment on platforms like Railway, sensitive data is managed using Environment Variables.


 
1. **Firebase Key:** Open your Firebase Service Account JSON file. **Copy the entire JSON content** into a single environment variable named `FIREBASE_KEY_CONTENT`.

2. **Discord Token:** Set your bot token in an environment variable named `DISCORD_BOT_TOKEN`.

<table>
 <tr>
   <td>
<strong>Variable Name</strong>
   </td>
   <td><strong>Value</strong>
   </td>
   <td><strong>Purpose</strong>
   </td>
  </tr>
  <tr>
   <td>DISCORD_BOT_TOKEN
   </td>
   <td>Your Bot's Token
   </td>
   <td>Required for the bot to log into Discord.
   </td>
  </tr>
  <tr>
   <td>FIREBASE_KEY_CONTENT
   </td>
   <td><strong>Entire JSON content</strong>
   </td>
   <td>Securely initializes the Firebase Admin SDK.
   </td>
  </tr>
</table>



### Running the Bot (Local Testing)  



1. **Install Dependencies:** \
`pip install discord.py firebase-admin python-dotenv aiofiles \`

2. **Run the Script:** \
`python "LFG Bot.py" \`



## 📋 Command Reference


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
   <td>Subscribe to notifications for a specific game in <em>this server</em>.
 </td>
   <td>/addgame game: Helldivers 2
   </td>
  </tr>
  <tr>
   <td><strong>/removegame</strong>
   </td>
   <td>Unsubscribe from a game's notification list in <em>this server</em>.
   </td>
   <td>/removegame game: Destiny 2
   </td>
  </tr>
  <tr>
   <td><strong>/lfg</strong>
   </td>
   <td>Ping all subscribers for a game <strong>in this server</strong>. Starts a new dedicated thread automatically.
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
   <td>Shows all games that currently have at least one subscriber in the database for <em>this server</em>.
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



## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated!


1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature`').
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.
