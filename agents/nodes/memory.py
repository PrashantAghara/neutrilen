import base64
from agents.state import AgentState
from db import save_food_logs_bulk, fetch_daily_total, image_hash, save_image_cache


def memory_node(state: AgentState) -> dict:
    print("Memory node")
    try:
        entries = state["nutrition_entries"]
        if not entries:
            print("  No entries to save — skipping")
            return {"daily_total": dict(fetch_daily_total(state["user_id"]))}
        rows = [
            {
                "user_id": state["user_id"],
                "food_name": e.food_name,
                "calories": e.calories,
                "protein": e.protein,
                "carbs": e.carbs,
                "fat": e.fat,
                "portion_g": e.portion_g,
                "image_b64": state["image_b64"],
                "confidence": e.confidence,
                "source": e.source,
            }
            for e in entries
        ]
        saved = save_food_logs_bulk(rows)
        print(f"  Saved {len(saved)} row(s) to food_logs")

        if state.get("image_b64"):
            raw_bytes = base64.b64decode(state["image_b64"])
            h = image_hash(raw_bytes)
            first = entries[0]
            save_image_cache(
                img_hash=h,
                user_id=state["user_id"],
                food_name=first.food_name,
                calories=first.calories,
                protein=first.protein,
                carbs=first.carbs,
                fat=first.fat,
                portion_g=first.portion_g,
                confidence=first.confidence,
                source=first.source,
            )
            print(f"  Image cached (hash: {h[:8]}...)")

        daily = fetch_daily_total(state["user_id"])
        print(
            f"  Today's total → {daily['total_calories']} kcal | "
            f"P {daily['total_protein']}g C {daily['total_carbs']}g F {daily['total_fat']}g"
        )
        print("✅  Memory node complete")
        return {"daily_total": dict(daily), "error": None}
    except Exception as e:
        print(f"❌  Memory node failed: {e}")
        return {"daily_total": {}, "error": str(e)}
