from agents.state import AgentState
from db import update_streak


def streak_node(state: AgentState) -> dict:
    """
    Increment streak if user logged food today.
    Award milestone badges at 3 / 7 / 14 / 30 days.
    """
    print("Running streak_node...")
    try:
        row = update_streak(state["user_id"])

        print(f"✅  Streak: {row['current']} day(s) | Longest: {row['longest']}")
        for days, key in [
            (3, "badge_3"),
            (7, "badge_7"),
            (14, "badge_14"),
            (30, "badge_30"),
        ]:
            if row[key]:
                print(f"  🏅  {days}-day badge earned!")

        return {"streak": row["current"], "error": None}

    except Exception as e:
        print(f"❌  Streak node failed: {e}")
        return {"streak": 0, "error": str(e)}
