# services/openai_service.py
import os
from dotenv import load_dotenv
from openai import OpenAI
from database.db import get_user_preferences

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("Missing OpenAI API key; please set OPENAI_API_KEY in your .env")

client = OpenAI(api_key=api_key)

def build_recipe_prompt(req):
    prefs = get_user_preferences(req.user_id)
    return (
        f"Create a {req.meal_type} recipe for {req.servings} servings "
        f"under {req.time_limit} minutes in {req.cuisine} cuisine. "
        f"Dietary restrictions: {', '.join(prefs.dietary_restrictions)}. "
        f"Disliked ingredients: {', '.join(prefs.disliked_ingredients)}. "
        f"Budget range: {prefs.budget_range} THB. "
        f"Available ingredients: {', '.join(req.available_ingredients)}. "
        "List ingredients and step-by-step instructions."
    )

def generate_recipe(prompt: str) -> str:
    resp = client.chat.completions.create(
      model="gpt-4",
      messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content
