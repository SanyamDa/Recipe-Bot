# models/recipe_request.py
from dataclasses import dataclass
from typing import List

@dataclass
class RecipeRequest:
    user_id: int
    cuisine: str
    meal_type: str
    servings: int
    time_limit: int
    available_ingredients: List[str]
