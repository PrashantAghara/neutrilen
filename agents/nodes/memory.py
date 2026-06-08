import uuid
import base64
from agents.state import AgentState
from db import (
    save_food_logs_bulk,
    fetch_daily_total,
    image_hash,
    save_image_cache,
)


def memory_node(state: AgentState) -> dict:
    print("Running memory_node...")
    try:
        entries = state["nutrition_entries"]

        if not entries:
            print("  No entries to save — skipping")
            return {"daily_total": dict(fetch_daily_total(state["user_id"]))}

        # One meal_id for all ingredients from this photo
        meal_id = str(uuid.uuid4())

        rows = [
            {
                "user_id": state["user_id"],
                "meal_id": meal_id,
                "dish_name": state["dish_name"],
                "food_name": e.food_name,
                "calories": e.calories,
                "protein": e.protein,
                "carbs": e.carbs,
                "fat": e.fat,
                "portion_g": e.portion_g,
                "image_b64": state["image_b64"],
                "confidence": e.confidence,
                "source": e.source,
                "is_veg": e.is_veg,  # ← new
                "flagged": e.flagged,  # ← new
            }
            for e in entries
        ]
        saved = save_food_logs_bulk(rows)
        print(f"  Saved {len(saved)} row(s) to food_logs (meal_id: {meal_id[:8]}...)")

        if state.get("image_b64"):
            raw_bytes = base64.b64decode(state["image_b64"])
            h = image_hash(raw_bytes)
            first = entries[0]
            save_image_cache(
                img_hash=h,
                user_id=state["user_id"],
                food_name=state["dish_name"],
                calories=sum(e.calories for e in entries),
                protein=sum(e.protein for e in entries),
                carbs=sum(e.carbs for e in entries),
                fat=sum(e.fat for e in entries),
                confidence=first.confidence,
                source=first.source,
            )
            print(f"  Image cached (hash: {h[:8]}...)")

        daily = fetch_daily_total(state["user_id"])
        print(f"  Today's total → {daily['total_calories']} kcal")
        print("✅  Memory node complete")
        return {"daily_total": dict(daily), "error": None}

    except Exception as e:
        print(f"❌  Memory node failed: {e}")
        return {"daily_total": {}, "error": str(e)}
