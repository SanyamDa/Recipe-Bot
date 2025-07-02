# models/user_preferences.py
from dataclasses import dataclass
from typing import List

@dataclass
class UserPreferences:
    dietary_restrictions: List[str]
    skill_level: str
    disliked_ingredients: List[str]
    budget_range: str
