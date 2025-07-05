# database/db.py
import sqlite3
from pathlib import Path
from models.user_preferences import UserPreferences
from models.recipe_request import RecipeRequest

DB_PATH = Path(__file__).parent / "bot.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    print("[DEBUG] Initializing database...")
    conn = get_connection()
    c = conn.cursor()
    
    # Check if users table exists
    c.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='users'
    """)
    
    if not c.fetchone():
        # Create users table if it doesn't exist
        c.execute("""
          CREATE TABLE users (
            user_id INTEGER PRIMARY KEY,
            dietary TEXT,
            skill TEXT,
            budget TEXT
          )
        """)
    
    # Check if recipes table exists
    c.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='recipes'
    """)
    
    if not c.fetchone():
        # Create recipes table if it doesn't exist
        c.execute("""
          CREATE TABLE recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            body TEXT NOT NULL,
            is_fav BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, name) ON CONFLICT REPLACE,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
          )
        """)
    else:
        # Check if is_fav column exists, add it if not
        c.execute("PRAGMA table_info(recipes)")
        columns = [col[1] for col in c.fetchall()]
        if 'is_fav' not in columns:
            c.execute("ALTER TABLE recipes ADD COLUMN is_fav BOOLEAN DEFAULT 0")
    
    # Check if recipe_requests table exists and create if it doesn't
    c.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='recipe_requests'
    """)
    
    if not c.fetchone():
        # Create recipe_requests table
        c.execute("""
          CREATE TABLE recipe_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            cuisine TEXT,
            meal TEXT,
            servings INTEGER,
            time_limit INTEGER,
            ingredients TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
          )
        """)
    
    conn.commit()
    print("[DEBUG] Database initialized successfully")
    conn.close()

def save_recipe(user_id: int, name: str, body: str) -> int:
    """Save a recipe to the database.
    
    Args:
        user_id: The ID of the user who owns the recipe
        name: The name of the recipe (will be cleaned up)
        body: The full recipe text
        
    Returns:
        int: The ID of the saved recipe
    """
    # Clean up the recipe name by removing any leading numbers or dots
    import re
    cleaned_name = re.sub(r'^\d+[\.\s]*', '', name)  # Remove leading numbers and dots
    cleaned_name = re.sub(r'^Title[:\s]*', '', cleaned_name, flags=re.IGNORECASE)  # Remove 'Title:'
    cleaned_name = cleaned_name.strip()  # Remove any extra whitespace
    
    print(f"[DEBUG] Saving recipe. Original name: '{name}', Cleaned name: '{cleaned_name}'")
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # First ensure the user exists in the users table
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,)
        )
        
        # Then insert or update the recipe
        cursor.execute(
            """
            INSERT INTO recipes (user_id, name, body, is_fav, created_at)
            VALUES (?, ?, ?, 0, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, name) DO UPDATE SET 
                body = excluded.body,
                created_at = CURRENT_TIMESTAMP
            RETURNING id
            """,
            (user_id, cleaned_name, body)
        )
        
        result = cursor.fetchone()
        if result:
            recipe_id = result[0]
            print(f"[DEBUG] Recipe {recipe_id} saved/updated successfully for user {user_id}")
            conn.commit()
            return recipe_id
        else:
            # If no row was returned (shouldn't happen with RETURNING), try to get the ID
            cursor.execute(
                "SELECT id FROM recipes WHERE user_id = ? AND name = ?",
                (user_id, cleaned_name)
            )
            result = cursor.fetchone()
            if result:
                return result[0]
            raise Exception("Failed to retrieve recipe ID after insert/update")
            
    except Exception as e:
        print(f"[ERROR] Error saving recipe: {e}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        conn.rollback()
        raise
    finally:
        conn.close()

def set_favorite(user_id: int, recipe_id: int, fav: bool = True) -> bool:
    """
    Set or unset a recipe as favorite for a user.
    
    Args:
        user_id: The ID of the user
        recipe_id: The ID of the recipe
        fav: Whether to set as favorite (True) or unfavorite (False)
        
    Returns:
        bool: True if the update was successful, False otherwise
    """
    print(f"[DEBUG] Setting favorite: user_id={user_id}, recipe_id={recipe_id}, fav={fav}")
    conn = get_connection()
    try:
        # First verify the recipe exists and belongs to the user
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name FROM recipes WHERE id = ? AND user_id = ?",
            (recipe_id, user_id)
        )
        recipe = cursor.fetchone()
        
        if not recipe:
            print(f"[ERROR] Recipe {recipe_id} not found for user {user_id}")
            return False
            
        # Update the favorite status
        cursor.execute(
            "UPDATE recipes SET is_fav = ? WHERE id = ? AND user_id = ?",
            (1 if fav else 0, recipe_id, user_id)
        )
        
        rows_affected = cursor.rowcount
        print(f"[DEBUG] Updated favorite status for recipe {recipe[0]} ("
              f"{recipe[1]}): {fav}, Rows affected: {rows_affected}")
              
        conn.commit()
        return rows_affected > 0
        
    except Exception as e:
        print(f"[ERROR] Error in set_favorite: {e}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def clear_favorites(user_id: int) -> bool:
    """
    Clear all favorites for a user.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"[DEBUG] Clearing all favorites for user_id={user_id}")
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE recipes SET is_fav = 0 WHERE user_id = ?",
            (user_id,)
        )
        changes = conn.total_changes
        conn.commit()
        print(f"[DEBUG] Cleared {changes} favorites for user {user_id}")
        return changes > 0
    except Exception as e:
        print(f"[ERROR] Error clearing favorites: {e}")
        return False
    finally:
        conn.close()

def list_favorites(user_id: int) -> list[str]:
    """
    Get a list of favorite recipe names for a user.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        List of recipe names that are marked as favorites
    """
    print(f"[DEBUG] list_favorites called for user_id={user_id}")
    conn = get_connection()
    try:
        # First, verify the table structure
        cur = conn.cursor()
        
        # Ensure the is_fav column exists
        cur.execute("PRAGMA table_info(recipes)")
        columns = [col[1] for col in cur.fetchall()]
        
        if 'is_fav' not in columns:
            print("[WARNING] 'is_fav' column not found in recipes table")
            try:
                cur.execute("ALTER TABLE recipes ADD COLUMN is_fav BOOLEAN DEFAULT 0")
                conn.commit()
                print("[DEBUG] Successfully added 'is_fav' column")
            except Exception as e:
                print(f"[ERROR] Failed to add 'is_fav' column: {e}")
                return []
        
        # Query for favorites - ensure we're only getting non-empty names
        print(f"[DEBUG] Querying favorites for user_id={user_id}")
        cur.execute(
            "SELECT name FROM recipes WHERE user_id = ? AND is_fav = 1 AND name IS NOT NULL AND name != ''",
            (user_id,)
        )
        
        # Clean up the recipe names and filter out any empty ones
        recipes = [row[0].strip() for row in cur.fetchall() if row[0] and row[0].strip()]
        
        # Debug output
        print(f"[DEBUG] Found {len(recipes)} favorites: {recipes}")
        
        # Verify the data in the database
        cur.execute("SELECT id, name, is_fav FROM recipes WHERE user_id = ?", (user_id,))
        all_recipes = cur.fetchall()
        print(f"[DEBUG] All recipes for user {user_id}: {[(r[1], r[2]) for r in all_recipes]}")
        
        return recipes
    except Exception as e:
        print(f"[ERROR] Error in list_favorites: {e}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return []
    finally:
        conn.close()

def get_recipe(user_id: int, name: str) -> str | None:
    conn = get_connection()
    cur  = conn.execute(
        "SELECT body FROM recipes WHERE user_id=? AND name=?",
        (user_id, name)
    )
    row = cur.fetchone(); conn.close()
    return row[0] if row else None

def set_user_preferences(user_id: int, prefs: UserPreferences):
    print(f"[DEBUG] Setting preferences for user {user_id}")
    print(f"[DEBUG] Preferences: {prefs}")
    
    conn = get_connection()
    cur = conn.cursor()
    
    dietary_str = ",".join(prefs.dietary_restrictions) if prefs.dietary_restrictions else ""
    print(f"[DEBUG] Dietary string to save: {dietary_str}")
    
    try:
        cur.execute("""
            UPDATE users
               SET dietary = ?,
                   skill   = ?,
                   budget  = ?
             WHERE user_id = ?
        """, (
            dietary_str,
            prefs.skill_level,
            prefs.budget_range,
            user_id
        ))
        print(f"[DEBUG] Rows updated: {cur.rowcount}")

        if cur.rowcount == 0:
            print("[DEBUG] No existing user found, inserting new record")
            dietary_str = ",".join(prefs.dietary_restrictions) if prefs.dietary_restrictions else ""
            cur.execute("""
                INSERT INTO users (user_id, dietary, skill, budget)
                VALUES (?, ?, ?, ?)
            """, (
                user_id,
                dietary_str,
                prefs.skill_level,
                prefs.budget_range
            ))
            print("[DEBUG] Inserted new user record")

    except Exception as e:
        print(f"[DEBUG] An error occurred: {e}")
    finally:
        conn.commit()
        conn.close()

def get_user_preferences(user_id: int) -> UserPreferences:
    print(f"[DEBUG] Getting preferences for user {user_id}")
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT user_id, dietary, skill, budget
            FROM users
            WHERE user_id = ?
        """, (user_id,))

        row = cur.fetchone()
        print(f"[DEBUG] Retrieved row: {row}")

        # Default values for new users
        default_prefs = UserPreferences(
            dietary_restrictions=[],
            skill_level="beginner",
            budget_range="medium"
        )

        if not row or not any([row[1], row[2], row[3]]):
            print("[DEBUG] No preferences found, returning defaults")
            return default_prefs

        dietary = row[1].split(",") if row[1] else []
        preferences = UserPreferences(
            dietary_restrictions=dietary,
            skill_level=row[2] or "beginner",
            budget_range=row[3] or "medium"
        )
        print(f"[DEBUG] Returning preferences: {preferences}")
        return preferences

    except Exception as e:
        print(f"[DEBUG] Error getting preferences: {e}")
        # Return default preferences on error
        return UserPreferences(
            dietary_restrictions=[],
            skill_level="beginner",
            budget_range="medium"
        )
    finally:
        if conn:
            conn.close()

def set_recipe_request(user_id: int, req: RecipeRequest):
    print(f"[DEBUG] Saving recipe request for user {user_id}: {req}")
    conn = None
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO recipe_requests (user_id, cuisine, meal, servings, time_limit, ingredients)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            req.cuisine,
            req.meal_type,
            req.servings,
            req.time_limit,
            ",".join(req.available_ingredients) if hasattr(req, 'available_ingredients') and req.available_ingredients else ""
        ))
        conn.commit()
        print("[DEBUG] Recipe request saved successfully")
    except Exception as e:
        print(f"[DEBUG] Error saving recipe request: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
