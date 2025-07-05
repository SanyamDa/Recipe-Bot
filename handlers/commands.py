# handlers/commands.py

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from database.db import list_favorites, get_recipe, clear_favorites

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Recipe Bot!\n\n"
        "/onboard — Set or Change your static preferences\n"
        "/recipe — Generate a recipe\n"
        "/preferences — View your saved preferences\n"
        "/help — Show this menu again\n"
        "/favorites — View your saved favorites\n"
        "/clear_favorites — Remove all favorites\n"
        "/specific <recipe name> — View a specific recipe\n"
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

async def favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print(f"[DEBUG] Favorites command called by user {user_id}")
    
    # Get favorites from database
    names = list_favorites(user_id)
    print(f"[DEBUG] Retrieved favorites for user {user_id}: {names}")
    
    # Debug: Check what's in the recipes table
    from database.db import get_connection
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name, is_fav FROM recipes WHERE user_id = ?", (user_id,))
        recipes = cur.fetchall()
        print(f"[DEBUG] All recipes for user {user_id}: {recipes}")
    except Exception as e:
        print(f"[ERROR] Error checking recipes table: {e}")
    finally:
        conn.close()
    
    if not names:
        await update.message.reply_text("No favorites yet. Use ⭐ after a recipe.")
        return
    
    # Clean up recipe names by removing numbers and dots at the start
    import re
    cleaned_names = []
    for name in names:
        # Remove any leading numbers followed by dots or spaces
        cleaned = re.sub(r'^\d+[\.\s]*', '', name).strip()
        cleaned_names.append(cleaned)
    
    # Create bullet points with cleaned names
    bullets = "\n".join(f"• {name}" for name in cleaned_names)
    await update.message.reply_text(f"📚 Your favorites\n{bullets}")

async def clear_favorites_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all favorites for the user."""
    user_id = update.effective_user.id
    success = clear_favorites(user_id)
    
    if success:
        await update.message.reply_text("✅ All favorites have been cleared.")
    else:
        await update.message.reply_text("❌ Failed to clear favorites. Please try again.")


async def specific(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usage: /specific <recipe name>")
    name = " ".join(context.args)
    body = get_recipe(update.effective_user.id, name)
    if body:
        await update.message.reply_text(body, disable_web_page_preview=True)
    else:
        await update.message.reply_text("Recipe not found. Check /favorites.")

COMMAND_HANDLERS = [
    CommandHandler('start', start),
    CommandHandler('help', help_command),
    CommandHandler('preferences', preferences),
    CommandHandler("favorites", favorites),
    CommandHandler("clear_favorites", clear_favorites_cmd),
    CommandHandler("specific",  specific),
]
