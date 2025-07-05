# handlers/conversations.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
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
from database.db             import set_user_preferences, set_recipe_request, save_recipe
from services.openai_service import build_recipe_prompt, generate_recipe

# ─── CONVERSATION STATES ─────────────────────────────────────────────────────
# Onboarding states
DIET, SKILL, BUDGET = range(3)

# Recipe generation states
R_CUISINE, R_MEAL, R_SERVINGS, R_TIME, R_INGREDIENTS = range(100, 105)

# ─── ONBOARDING OPTIONS ────────────────────────────────────────────────────────
DIET_CHOICES    = ["None", "Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Nut-Free"]
SKILL_CHOICES   = ["Beginner", "Intermediate", "Advanced"]
BUDGET_CHOICES  = ["100-200", "200-500", "500-1000"]

# ─── RECIPE GENERATION OPTIONS ───────────────────────────────────────────────
CUISINE_CHOICES = ["Italian", "Mexican", "Indian", "Chinese", "Thai", "Japanese", "American", "Mediterranean"]
MEAL_CHOICES = ["Breakfast", "Lunch", "Dinner", "Dessert", "Snack"]

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

    # Next: budget
    markup = ReplyKeyboardMarkup([[d] for d in BUDGET_CHOICES], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("💰 What is your budget range in THB per meal?", reply_markup=markup)
    return BUDGET

async def collect_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice not in BUDGET_CHOICES:
        return await update.message.reply_text(
            "Please choose a budget range.",
            reply_markup=ReplyKeyboardMarkup([[b] for b in BUDGET_CHOICES], one_time_keyboard=True, resize_keyboard=True)
        )
    context.user_data['budget'] = choice

    # Persist preferences
    user_id = update.effective_user.id
    prefs = UserPreferences(
        dietary_restrictions=[context.user_data['dietary']] if 'dietary' in context.user_data else ["None"],
        skill_level=context.user_data.get('skill', 'Intermediate'),
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
        BUDGET:   [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_budget)],
    },
    fallbacks=[CommandHandler("cancel", cancel_onboard)],
    name="onboard_conversation",
)

# ─── RECIPE OPTIONS ─────────────────────────────────────────────────────────
CUISINE_CHOICES  = ["Thai", "Italian", "Mexican", "Indian", "Other"]
MEAL_CHOICES     = ["Breakfast", "Lunch", "Dinner", "Snack"]
SERVINGS_CHOICES = ["1", "2", "4", "6+"]
TIME_CHOICES     = ["15", "30", "45", "60"]

async def recipe_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ReplyKeyboardMarkup([[c] for c in CUISINE_CHOICES],
                             one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("🍽️ What cuisine?", reply_markup=kb)
    return R_CUISINE

async def collect_cuisine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice not in CUISINE_CHOICES:
        await update.message.reply_text(
            "Please choose a cuisine from the keyboard ⬇️",
            reply_markup=ReplyKeyboardMarkup([[c] for c in CUISINE_CHOICES],
                                             one_time_keyboard=True, resize_keyboard=True)
        )
        return R_CUISINE       # stay in the same state

    context.user_data['cuisine'] = choice
    kb = ReplyKeyboardMarkup([[m] for m in MEAL_CHOICES],
                             one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("🍽️ What type of meal?", reply_markup=kb)
    return R_MEAL

async def collect_meal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice not in MEAL_CHOICES:
        await update.message.reply_text(
            "Select a meal type from the keyboard ⬇️",
            reply_markup=ReplyKeyboardMarkup([[m] for m in MEAL_CHOICES],
                                             one_time_keyboard=True, resize_keyboard=True)
        )
        return R_MEAL

    context.user_data['meal'] = choice
    kb = ReplyKeyboardMarkup([[s] for s in SERVINGS_CHOICES],
                             one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("👥 How many servings?", reply_markup=kb)
    return R_SERVINGS

async def collect_servings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice not in SERVINGS_CHOICES:
        await update.message.reply_text(
            "Select servings from the keyboard ⬇️",
            reply_markup=ReplyKeyboardMarkup([[s] for s in SERVINGS_CHOICES],
                                             one_time_keyboard=True, resize_keyboard=True)
        )
        return R_SERVINGS

    context.user_data['servings'] = int(choice.rstrip('+'))
    kb = ReplyKeyboardMarkup([[t] for t in TIME_CHOICES],
                             one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("⏱️ Max cook time (minutes)?", reply_markup=kb)
    return R_TIME

async def collect_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice not in TIME_CHOICES:
        await update.message.reply_text(
            "Select a time limit from the keyboard ⬇️",
            reply_markup=ReplyKeyboardMarkup([[t] for t in TIME_CHOICES],
                                             one_time_keyboard=True, resize_keyboard=True)
        )
        return R_TIME

    context.user_data['time'] = int(choice)
    await update.message.reply_text(
        "📋 List your ingredients (comma-separated):",
        reply_markup=ReplyKeyboardRemove()
    )
    return R_INGREDIENTS

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

    prompt  = build_recipe_prompt(req)
    recipe  = generate_recipe(prompt)
    title_line = recipe.splitlines()[0].lstrip("#* ").strip() 
    
    # Save the recipe and get its ID
    recipe_id = save_recipe(user_id, title_line, recipe)
    await update.message.reply_text(recipe)

    # Create favorite button with recipe ID
    fav_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "⭐ Add to favorites",
            callback_data=f"fav|{recipe_id}"
        )]
    ])
    await update.message.reply_text("Save this recipe?", reply_markup=fav_kb)

    context.user_data.clear()
    return ConversationHandler.END  

async def cancel_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Recipe canceled. Use /recipe to try again.",
                                    reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

recipe_conv = ConversationHandler(
    entry_points=[CommandHandler("recipe", recipe_entry)],
    states={
        R_CUISINE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_cuisine)],
        R_MEAL:        [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_meal)],
        R_SERVINGS:    [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_servings)],
        R_TIME:        [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_time)],
        R_INGREDIENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_ingredients)],
    },
    fallbacks=[CommandHandler("cancel", cancel_recipe)],
    name="recipe_conversation",
)