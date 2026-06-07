import os
import json
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from agents.state import AgentState
from agents.prompts import VISION_PROMPT

vision_llm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    api_key=os.environ["GROQ_API_KEY"],
    temperature=0.1,
    max_tokens=1024,
)


def vision_node(state: AgentState):
    print("Running vision Node...")
    try:
        msg = HumanMessage(
            content=[
                {"type": "text", "text": VISION_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{state['image_b64']}"
                    },
                },
            ]
        )
        response = vision_llm.invoke([msg])
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        parsed = json.loads(raw)

        dish_is_veg = parsed.get("is_veg", True)

        print("\nIdentified items:")
        for f in parsed.get("foods", []):
            veg_icon = "🟢" if f.get("is_veg", True) else "🔴"
            print(f"    {veg_icon} {f['name']:25s} (conf: {f['confidence']:.2f})")

        dish = parsed.get("dish_name", "Unknown Dish")
        cuisine = parsed.get("cuisine", "Unknown")
        veg_label = "Vegetarian" if dish_is_veg else "Non-Vegetarian"

        print(f"\n✅  Vision node complete — {dish} ({cuisine}) [{veg_label}]")
        return {
            "raw_vision_text": raw,
            "dish_name": dish,
            "cuisine": cuisine,
            "error": None,
        }
    except Exception as e:
        print(f"❌  Vision node failed: {e}")
        return {"raw_vision_text": "", "error": str(e)}
