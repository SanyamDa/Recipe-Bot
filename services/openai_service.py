# services/openai_service.py
import os
from dotenv import load_dotenv
from openai import OpenAI
from models.recipe_request   import RecipeRequest
from models.user_preferences import UserPreferences
from database.db import get_user_preferences

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("Missing OpenAI API key; please set OPENAI_API_KEY in your .env")
    
client = OpenAI(api_key=api_key)

COMMON_STAPLES = [
    "salt", "black pepper", "sugar", "cooking oil (neutral)",
    "basic dry spices (cumin, paprika, chili flakes)",
    "all-purpose flour", "baking powder", "soy sauce",
    "garlic", "onion"
]

CUISINE_BASES = {
    "Thai":     ["fish sauce", "palm sugar", "lime", "lemongrass", "cilantro"],
    "Italian":  ["olive oil", "garlic", "onion", "dried oregano", "parmesan"],
    "Mexican":  ["cumin", "dried oregano", "lime", "chilies", "cilantro"],
    "Indian":   ["ginger-garlic paste", "turmeric", "garam masala", "cumin seeds"],
    "Other":    []
}

def build_recipe_prompt(req: RecipeRequest) -> str:
    """Return a rich prompt for GPT that assumes common staples + cuisine bases."""

    # fallback in case user has no prefs stored yet
    prefs = get_user_preferences(req.user_id) or UserPreferences(
        dietary_restrictions=[], skill_level="Intermediate",
        disliked_ingredients=[], budget_range="no budget"
    )

    pantry_assumed = COMMON_STAPLES + CUISINE_BASES.get(req.cuisine, [])
    pantry_str     = ", ".join(pantry_assumed)

    prompt = (
        f"### Task\n"
        f"You are a professional chef & nutritionist.  Create ONE {req.meal_type.lower()} recipe "
        f"for {req.servings} servings.  It must take no more than {req.time_limit} minutes "
        f"of active time and should belong to **{req.cuisine} cuisine**.\n\n"

        f"### Constraints\n"
        f"- Budget: around {prefs.budget_range} THB in Thailand.\n"
        f"- Dietary restrictions: {', '.join(prefs.dietary_restrictions) or 'none'}.\n"
        f"- Assume the user ALREADY HAS these common pantry items: {pantry_str}.\n"
        f"- They ALSO have: {', '.join(req.available_ingredients) or 'no extra ingredients listed'}.\n"
        f"- Skill level: {prefs.skill_level}; keep steps at that difficulty.\n\n"

        f"### Output format (markdown)\n"
        f"1. Title: \n\n"
        f"2. Total time (prep + cook)\n\n"
        f"3. Ingredients  \n"
        f" - ingredients to buy\n"
        f"4. Step-by-step instructions (numbered)\n"
        f"5. Serving & plating tips\n"
        f"6. Estimated nutrition per serving (kcal, protein, carbs, fat)\n"
        f"7. Budget breakdown (approx. THB)\n"
    )
    return prompt


def generate_recipe(prompt: str) -> str:
    resp = client.chat.completions.create(
      model="gpt-4",
      messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content
