import threading
import logging
from src.database import DatabaseManager
from src.bot_app import create_bot_app
from src.gui_app import App

def run_bot():
    app = create_bot_app()
    # stop_signals=None prevents it from catching SIGINT and killing the main thread
    app.run_polling(stop_signals=None)

def main():
    # 1. Init DB
    db = DatabaseManager()
    print("Database Initialized.")

    # 2. Start Bot in Thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("Bot started in background.")

    # 3. Start GUI
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.quit) # Ensure clean exit
    app.mainloop()
    print("Application closed.")

if __name__ == "__main__":
    main()
