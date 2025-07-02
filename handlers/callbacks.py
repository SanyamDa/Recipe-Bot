# handlers/callbacks.py

from telegram import Update
from telegram.ext import ContextTypes

async def budget_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delegate an inline-button tap to the budget_choice step."""
    query = update.callback_query
    await query.answer()
    context.user_data['budget'] = query.data

    # Now hand off to the onboard flow’s budget_choice
    from handlers.conversations import budget_choice
    return await budget_choice(update, context)

async def cuisine_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delegate an inline-button tap to the cuisine_choice step."""
    query = update.callback_query
    await query.answer()
    context.user_data['cuisine'] = query.data

    from handlers.conversations import cuisine_choice
    return await cuisine_choice(update, context)

async def meal_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delegate an inline-button tap to the meal_choice step."""
    query = update.callback_query
    await query.answer()
    context.user_data['meal'] = query.data

    from handlers.conversations import meal_choice
    return await meal_choice(update, context)

async def servings_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delegate an inline-button tap to the servings_choice step."""
    query = update.callback_query
    await query.answer()
    # coerce to int, default 1 if non-digit
    context.user_data['servings'] = int(query.data) if query.data.isdigit() else 1

    from handlers.conversations import servings_choice
    return await servings_choice(update, context)

async def time_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delegate an inline-button tap to the time_choice step."""
    query = update.callback_query
    await query.answer()
    context.user_data['time'] = int(query.data)

    from handlers.conversations import time_choice
    return await time_choice(update, context)
