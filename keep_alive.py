    from flask import Flask
    from threading import Thread

    # Set up a tiny Flask server to listen for pings from UptimeRobot
    app = Flask('')

    @app.route('/')
    def home():
        # This message confirms the server is running when UptimeRobot pings it
        return "LFG Bot is Alive!"

    def run():
      # Host the server on 0.0.0.0 (all interfaces) and port 8080 (Replit default)
      app.run(host='0.0.0.0', port=8080)

    def keep_alive():
      # Run the server in a separate thread so it doesn't block the main bot
      t = Thread(target=run)
      t.start()
    
