import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import AgentState
from agents.prompts import ADVICE_SYSTEM_PROMPT

advice_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.environ["GROQ_API_KEY"],
    temperature=0.4,
    max_tokens=256,
)


def goal_node(state: AgentState) -> dict:
    print("Running goal_node...")
    try:
        total = state["daily_total"]
        goals = state["goals"]
        preference = state.get("diet_preference", "both")
        entries = state["nutrition_entries"]

        remaining_kcal = goals["calories"] - total.get("total_calories", 0)
        remaining_protein = goals["protein"] - total.get("total_protein", 0)
        remaining_carbs = goals["carbs"] - total.get("total_carbs", 0)
        remaining_fat = goals["fat"] - total.get("total_fat", 0)

        # Build flagged items warning if any
        flagged_items = [e.food_name for e in entries if e.flagged]
        flag_warning = ""
        if flagged_items:
            flag_warning = f"""
        ⚠️  WARNING: The following non-vegetarian items were detected in a 
        meal logged by a vegetarian user: {", ".join(flagged_items)}.
        Mention this concern kindly in your advice.
        """

        if preference == "veg":
            protein_suggestion = "dal, paneer, chickpeas, tofu, or Greek yogurt"
        elif preference == "non_veg":
            protein_suggestion = "chicken breast, eggs, fish, or paneer"
        else:
            protein_suggestion = "chicken, eggs, dal, paneer, or fish"

        prompt = f"""
        The user has eaten so far today:
        - Calories : {total.get("total_calories", 0):.0f} kcal (goal: {goals["calories"]}, remaining: {remaining_kcal:.0f})
        - Protein  : {total.get("total_protein", 0):.1f}g  (goal: {goals["protein"]}g,  remaining: {remaining_protein:.1f}g)
        - Carbs    : {total.get("total_carbs", 0):.1f}g  (goal: {goals["carbs"]}g,    remaining: {remaining_carbs:.1f}g)
        - Fat      : {total.get("total_fat", 0):.1f}g  (goal: {goals["fat"]}g,      remaining: {remaining_fat:.1f}g)

        Diet preference: {preference}
        Suggest only {preference if preference != "both" else "any"} food sources for protein.
        Good protein sources for this user: {protein_suggestion}

        {flag_warning}

        Write a friendly 1-2 sentence summary and one specific meal suggestion
        that fits their diet preference.
        """

        response = advice_llm.invoke(
            [
                SystemMessage(content=ADVICE_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]
        )
        advice = response.content.strip()
        print(f"✅  Goal node complete\n  Advice: {advice}")
        return {"advice": advice, "error": None}

    except Exception as e:
        print(f"❌  Goal node failed: {e}")
        return {"advice": "", "error": str(e)}
