# bot.py
import os
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
)

from handlers.commands       import COMMAND_HANDLERS
from handlers.conversations  import onboard_conv, recipe_conv
from database.db             import init_db

def main():
    # 1) Load env & init DB
    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        raise RuntimeError("Missing TELEGRAM_TOKEN in .env")
    application.run_polling()

if __name__ == "__main__":
    main()
