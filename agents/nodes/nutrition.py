import os
import json
import base64
import requests
from agents.state import AgentState, NutritionEntry

HF_API_URL = "https://router.huggingface.co/hf-inference/models/nateraw/food"
HF_HEADERS = {"Authorization": f"Bearer {os.environ.get('HF_TOKEN', '')}"}
CONFIDENCE_THRESHOLD = int(os.environ.get("CONFIDENCE_THRESHOLD"))


def hf_classify_food(image_b64: str) -> dict:
    images_bytes = base64.b64decode(image_b64)
    response = requests.post(
        HF_API_URL, headers=HF_HEADERS, data=images_bytes, timeout=15
    )
    results = response.json()
    print(results)
    if isinstance(results, list) and results:
        return {"label": results[0]["label"], "score": results[0]["score"]}
    return {"label": "unknown", "score": 0.0}


def nutrition_node(state: AgentState) -> dict:
    print("Running nutrition_node...")
    try:
        parsed = json.loads(state["raw_vision_text"])
        foods = parsed.get("foods", [])
        entries = []
        preference = state.get("diet_preference", "both")
        flagged = []

        for f in foods:
            confidence = float(f.get("confidence", 1.0))
            is_veg = f.get("is_veg", True)

            if confidence < CONFIDENCE_THRESHOLD:
                print(
                    f"  Low confidence ({confidence:.2f}) for '{f['name']}' — trying HF fallback"
                )
                hf = hf_classify_food(state["image_b64"])
                if hf["label"] != "unknown" and hf["score"] > confidence:
                    print(f"  HF override: '{hf['label']}' (score {hf['score']:.2f})")
                    f["name"] = hf["label"]
                    f["confidence"] = hf["score"]
                    f["source"] = "huggingface"

            item_flagged = False
            if preference == "veg" and not is_veg:
                item_flagged = True
                flagged.append(f["name"])
                print(f"  ⚠️  '{f['name']}' is non-veg — flagged for veg user")
            elif preference == "non_veg" and is_veg:
                pass

            entry = NutritionEntry(
                food_name=f.get("name", "unknown"),
                portion_g=f.get("portion_g"),
                calories=float(f.get("calories", 0)),
                protein=float(f.get("protein", 0)),
                carbs=float(f.get("carbs", 0)),
                fat=float(f.get("fat", 0)),
                confidence=float(f.get("confidence", 1.0)),
                source=f.get("source", "groq"),
                is_veg=is_veg,
                flagged=item_flagged,
            )
            entries.append(entry)

            veg_icon = "🟢" if is_veg else "🔴"
            flag_icon = " ⚠️ " if item_flagged else ""
            print(
                f"  {veg_icon}{flag_icon} {entry.food_name}: {entry.calories} kcal | "
                f"P {entry.protein}g C {entry.carbs}g F {entry.fat}g "
                f"(conf {entry.confidence:.2f})"
            )

        if flagged:
            print(f"\n  ⚠️  Non-veg items detected for veg user: {', '.join(flagged)}")

        print(f"\n✅  Nutrition node complete — {len(entries)} item(s) parsed")
        return {"nutrition_entries": entries, "error": None}

    except Exception as e:
        print(f"❌  Nutrition node failed: {e}")
        return {"nutrition_entries": [], "error": str(e)}
