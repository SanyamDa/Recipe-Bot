from telegram import Update
from telegram.ext import CallbackContext

def start_callback(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Welcome to Recipe Bot!\n"
        "Use /onboard to set your cooking preferences.\n"
        "Then try /recipe to get a recipe."
    )

def onboard_callback(update: Update, context: CallbackContext):
    # Kick off the onboarding conversation
    return 'ONBOARD_START'

def recipe_callback(update: Update, context: CallbackContext):
    # Generate and send recipe
    pass