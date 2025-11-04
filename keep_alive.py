from flask import Flask
from threading import Thread
import logging

# Disable default Flask logging to keep the console clean
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask('')

@app.route('/')
def home():
    """Simple health check endpoint."""
    return "LFG Bot is running!"

def run():
    """Runs the Flask server."""
    # Host on 0.0.0.0 for external access (needed for Replit/Railway)
    app.run(host='0.0.0.0', port=8080) 

def keep_alive():
    """Starts the Flask server in a separate thread."""
    t = Thread(target=run)
    t.start()
    print("Keep-alive server started on port 8080.")
    
