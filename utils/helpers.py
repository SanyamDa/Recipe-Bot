# utils/helpers.py
from telegram import ReplyKeyboardMarkup

from models.user_preferences import UserPreferences

def format_preferences(prefs: UserPreferences) -> str:
    return (
        f"Dietary: {', '.join(prefs.dietary_restrictions)}\n"
        f"Skill: {prefs.skill_level}\n"
        f"Disliked: {', '.join(prefs.disliked_ingredients)}\n"
        f"Budget: {prefs.budget_range} THB"
    )

def build_reply_keyboard(options: list) -> ReplyKeyboardMarkup:
    # one-button-per-row keyboard
    keyboard = [[opt] for opt in options]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
