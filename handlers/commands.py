# handlers/commands.py

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Recipe Bot!\n\n"
        "/onboard — Set your static preferences (dietary restrictions, skill level, disliked ingredients, budget)\n"
        "/recipe — Generate a recipe (you’ll pick cuisine, meal type, servings, time, ingredients)\n"
        "/preferences — View your saved preferences\n"
        "/help — Show this menu again"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def preferences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from database.db    import get_user_preferences
    from utils.helpers import format_preferences

    user_id = update.effective_user.id
    prefs   = get_user_preferences(user_id)

    if prefs:
        await update.message.reply_text(format_preferences(prefs))
    else:
        await update.message.reply_text(
            "You haven't set preferences yet. Use /onboard to get started."
        )
        
async def onboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from handlers.conversations import onboard_entry
    return await onboard_entry(update, context)

async def recipe_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from handlers.conversations import recipe_entry
    return await recipe_entry(update, context)

COMMAND_HANDLERS = [
    CommandHandler('start', start),
    CommandHandler('help', help_command),
    CommandHandler('preferences', preferences),
]
