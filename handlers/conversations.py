# handlers/conversations.py

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    ConversationHandler,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)
from models.user_preferences import UserPreferences
from models.recipe_request   import RecipeRequest
from database.db             import set_user_preferences, set_recipe_request
from services.openai_service import build_recipe_prompt, generate_recipe

# ─── ONBOARDING STATES ─────────────────────────────────────────────────────────
DIET, SKILL, DISLIKED, BUDGET = range(4)

# ─── ONBOARDING OPTIONS ────────────────────────────────────────────────────────
DIET_CHOICES    = ["None", "Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Nut-Free"]
SKILL_CHOICES   = ["Beginner", "Intermediate", "Advanced"]
DISLIKE_CHOICES = ["Cilantro", "Anchovies", "Onions", "None"]
BUDGET_CHOICES  = ["100-200", "200-500", "500-1000"]

# ─── STEP 0: ONBOARD ENTRY ─────────────────────────────────────────────────────
async def onboard_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[c] for c in DIET_CHOICES]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "🔧 Onboarding: Select your dietary restriction:",
        reply_markup=markup
    )
    return DIET

async def collect_dietary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice not in DIET_CHOICES:
        return await update.message.reply_text(
            "Please choose a dietary restriction from the keyboard.",
            reply_markup=ReplyKeyboardMarkup([[c] for c in DIET_CHOICES], one_time_keyboard=True, resize_keyboard=True)
        )
    context.user_data['dietary'] = choice

    # Next: skill
    markup = ReplyKeyboardMarkup([[s] for s in SKILL_CHOICES], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("👩‍🍳 What is your cooking skill level?", reply_markup=markup)
    return SKILL

async def collect_skill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice not in SKILL_CHOICES:
        return await update.message.reply_text(
            "Please choose a skill level from the keyboard.",
            reply_markup=ReplyKeyboardMarkup([[s] for s in SKILL_CHOICES], one_time_keyboard=True, resize_keyboard=True)
        )
    context.user_data['skill'] = choice

    # Next: dislikes
    markup = ReplyKeyboardMarkup([[d] for d in DISLIKE_CHOICES], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("❌ Which ingredient do you dislike?", reply_markup=markup)
    return DISLIKED

async def collect_disliked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice not in DISLIKE_CHOICES:
        return await update.message.reply_text(
            "Please choose an ingredient to dislike.",
            reply_markup=ReplyKeyboardMarkup([[d] for d in DISLIKE_CHOICES], one_time_keyboard=True, resize_keyboard=True)
        )
    context.user_data['disliked'] = choice

    # Next: budget
    markup = ReplyKeyboardMarkup([[b] for b in BUDGET_CHOICES], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("💰 What is your budget range in THB?", reply_markup=markup)
    return BUDGET

async def collect_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice not in BUDGET_CHOICES:
        return await update.message.reply_text(
            "Please select a budget range.",
            reply_markup=ReplyKeyboardMarkup([[b] for b in BUDGET_CHOICES], one_time_keyboard=True, resize_keyboard=True)
        )
    context.user_data['budget'] = choice

    # Persist preferences
    user_id = update.effective_user.id
    prefs = UserPreferences(
        dietary_restrictions=[context.user_data['dietary']],
        skill_level=context.user_data['skill'],
        disliked_ingredients=[context.user_data['disliked']],
        budget_range=context.user_data['budget']
    )
    set_user_preferences(user_id, prefs)

    await update.message.reply_text(
        "✅ Preferences saved! Use /onboard anytime to update.",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_onboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Onboarding canceled. Use /onboard to start again.",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

onboard_conv = ConversationHandler(
    entry_points=[ CommandHandler("onboard", onboard_entry) ],
    states={
        DIET:     [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_dietary)],
        SKILL:    [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_skill)],
        DISLIKED: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_disliked)],
        BUDGET:   [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_budget)],
    },
    fallbacks=[CommandHandler("cancel", cancel_onboard)],
    name="onboard_conversation",
)

# ─── RECIPE STATES & OPTIONS ──────────────────────────────────────────────────
CUISINE, MEAL, SERVINGS, TIME, INGREDIENTS = range(5)
CUISINE_CHOICES  = ["Thai", "Italian", "Mexican", "Indian", "Other"]
MEAL_CHOICES     = ["Breakfast", "Lunch", "Dinner", "Snack"]
SERVINGS_CHOICES = ["1", "2", "4", "6+"]
TIME_CHOICES     = ["15", "30", "45", "60"]

async def recipe_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    markup = ReplyKeyboardMarkup([[c] for c in CUISINE_CHOICES], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("🍽️ What cuisine?", reply_markup=markup)
    return CUISINE

async def collect_cuisine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice not in CUISINE_CHOICES:
        return await update.message.reply_text(
            "Choose a cuisine from the keyboard.",
            reply_markup=ReplyKeyboardMarkup([[c] for c in CUISINE_CHOICES], one_time_keyboard=True, resize_keyboard=True)
        )
    context.user_data['cuisine'] = choice
    markup = ReplyKeyboardMarkup([[m] for m in MEAL_CHOICES], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("⏰ What meal type?", reply_markup=markup)
    return MEAL

async def collect_meal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice not in MEAL_CHOICES:
        return await update.message.reply_text(
            "Select a meal type from the keyboard.",
            reply_markup=ReplyKeyboardMarkup([[m] for m in MEAL_CHOICES], one_time_keyboard=True, resize_keyboard=True)
        )
    context.user_data['meal'] = choice
    markup = ReplyKeyboardMarkup([[s] for s in SERVINGS_CHOICES], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("👥 How many servings?", reply_markup=markup)
    return SERVINGS

async def collect_servings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice not in SERVINGS_CHOICES:
        return await update.message.reply_text(
            "Select servings from the keyboard.",
            reply_markup=ReplyKeyboardMarkup([[s] for s in SERVINGS_CHOICES], one_time_keyboard=True, resize_keyboard=True)
        )
    context.user_data['servings'] = int(choice.rstrip('+'))
    markup = ReplyKeyboardMarkup([[t] for t in TIME_CHOICES], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("⏱️ Max cook time (minutes)?", reply_markup=markup)
    return TIME

async def collect_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice not in TIME_CHOICES:
        return await update.message.reply_text(
            "Select a time limit from the keyboard.",
            reply_markup=ReplyKeyboardMarkup([[t] for t in TIME_CHOICES], one_time_keyboard=True, resize_keyboard=True)
        )
    context.user_data['time'] = int(choice)
    await update.message.reply_text(
        "📋 List your ingredients (comma-separated):",
        reply_markup=ReplyKeyboardRemove()
    )
    return INGREDIENTS

async def collect_ingredients(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ingredients = update.message.text
    user_id = update.effective_user.id
    req = RecipeRequest(
        user_id               = user_id,
        cuisine               = context.user_data['cuisine'],
        meal_type             = context.user_data['meal'],
        servings              = context.user_data['servings'],
        time_limit            = context.user_data['time'],
        available_ingredients = [i.strip() for i in ingredients.split(',')]
    )
    set_recipe_request(user_id, req)
    prompt = build_recipe_prompt(req)
    recipe = generate_recipe(prompt)
    await update.message.reply_text(recipe)
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Recipe canceled. Use /recipe to try again.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

recipe_conv = ConversationHandler(
    entry_points=[ CommandHandler("recipe", recipe_entry) ], 
    states={
        CUISINE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_cuisine)],
        MEAL:        [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_meal)],
        SERVINGS:    [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_servings)],
        TIME:        [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_time)],
        INGREDIENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_ingredients)],
    },
    fallbacks=[CommandHandler("cancel", cancel_recipe)],
    name="recipe_conversation",
)