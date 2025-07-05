# bot.py
import os
import logging
from dotenv import load_dotenv
from handlers.callbacks import favorite_callback
from handlers.commands import COMMAND_HANDLERS
from handlers.conversations import onboard_conv, recipe_conv
from database.db import init_db
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,        # if you already have this
    CallbackQueryHandler,   # ← add this line
    filters                 # if you use filters directly in bot.py
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    # 1) Load env & init DB
    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        raise RuntimeError("Missing TELEGRAM_TOKEN in .env")
    
    # 2) Initialize database
    init_db()
    
    # 3) Create application and add handlers
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add command handlers
    for handler in COMMAND_HANDLERS:
        application.add_handler(handler)
    
    # Add conversation handlers
    application.add_handler(onboard_conv)
    application.add_handler(recipe_conv)
    
    # Start the bot
    logger.info("Starting bot...")
    application.add_handler(CallbackQueryHandler(favorite_callback, pattern=r"^fav\|"))
    application.run_polling()

if __name__ == "__main__":
    main()
