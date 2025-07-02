# database/db.py
import sqlite3
from pathlib import Path
from models.user_preferences import UserPreferences
from models.recipe_request import RecipeRequest

DB_PATH = Path(__file__).parent / "bot.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
      CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        dietary TEXT,
        skill TEXT,
        disliked TEXT,
        budget TEXT
      )
    """)
    c.execute("""
      CREATE TABLE IF NOT EXISTS recipes (
        user_id INTEGER,
        cuisine TEXT,
        meal TEXT,
        servings INTEGER,
        time_limit INTEGER,
        ingredients TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    """)
    conn.commit()
    conn.close()

def set_user_preferences(user_id: int, prefs: UserPreferences):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
      INSERT OR REPLACE INTO users
      (user_id, dietary, skill, disliked, budget)
      VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        ",".join(prefs.dietary_restrictions),
        prefs.skill_level,
        ",".join(prefs.disliked_ingredients),
        prefs.budget_range
    ))
    conn.commit()
    conn.close()

def get_user_preferences(user_id: int) -> UserPreferences:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT dietary, skill, disliked, budget FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    dietary, skill, disliked, budget = row
    return UserPreferences(
        dietary_restrictions = dietary.split(",") if dietary else [],
        skill_level          = skill,
        disliked_ingredients = disliked.split(",") if disliked else [],
        budget_range         = budget
    )

def set_recipe_request(user_id: int, req: RecipeRequest):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
      INSERT INTO recipes
      (user_id, cuisine, meal, servings, time_limit, ingredients)
      VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        req.cuisine,
        req.meal_type,
        req.servings,
        req.time_limit,
        ",".join(req.available_ingredients)
    ))
    conn.commit()
    conn.close()
