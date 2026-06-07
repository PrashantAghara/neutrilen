from typing import TypedDict, Optional
from pydantic import BaseModel


class NutritionEntry(BaseModel):
    food_name: str
    portion_g: Optional[float] = None
    calories: float
    protein: float
    carbs: float
    fat: float
    confidence: float = 1.0
    source: str = "groq"
    is_veg: bool = True
    flagged: bool = False


class AgentState(TypedDict):
    user_id: str
    image_b64: Optional[str]
    dish_name: str
    cuisine: str
    diet_preference: str
    raw_vision_text: str
    nutrition_entries: list[NutritionEntry]
    daily_total: dict
    goals: dict
    streak: int
    advice: str
    error: Optional[str]
