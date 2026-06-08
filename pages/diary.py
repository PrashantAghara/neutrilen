import streamlit as st
from datetime import date
from db import delete_food_log, fetch_today_logs
from db.queries import fetch_today_meals
from db.connection import get_db
from db.queries import get_cursor


def delete_meal(meal_id: str):
    """Delete all food_log rows for a meal_id."""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("DELETE FROM food_logs WHERE meal_id = %s", (meal_id,))


def render_meal_card(meal):
    """Render one meal as a card showing dish name + expandable ingredients."""

    time_str = str(meal["logged_at"])[11:16]
    source_label = {
        "groq": "🤖 AI",
        "huggingface": "🤗 HF",
        "manual": "✏️ Manual",
    }.get(meal["source"], meal["source"])

    with st.container():
        # Meal header row
        col_info, col_actions = st.columns([4, 1])

        with col_info:
            st.markdown(
                f"**🍽️ {meal['dish_name'] or 'Meal'}**  "
                f"<span style='color:#8B8FA8; font-size:12px;'>"
                f"{time_str}  ·  {source_label}  ·  "
                f"{meal['ingredient_count']} ingredients</span>",
                unsafe_allow_html=True,
            )

            # Macro summary row
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🔥 kcal", f"{meal['total_calories']:.0f}")
            with col2:
                st.metric("💪 Protein", f"{meal['total_protein']:.1f}g")
            with col3:
                st.metric("🌾 Carbs", f"{meal['total_carbs']:.1f}g")
            with col4:
                st.metric("🥑 Fat", f"{meal['total_fat']:.1f}g")

        with col_actions:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(
                "🗑️ Delete", key=f"del_{meal['meal_id']}", use_container_width=True
            ):
                delete_meal(meal["meal_id"])
                st.success("Meal deleted!")
                st.rerun()

        # Expandable ingredients list
        with st.expander(
            f"View {meal['ingredient_count']} ingredients", expanded=False
        ):
            for ing in meal["ingredients"]:
                veg_icon = "🟢"  # default veg — stored is_veg not in DB yet
                st.markdown(
                    f"{veg_icon} **{ing['food_name']}** — "
                    f"🔥 {ing['calories']:.0f} kcal  "
                    f"💪 P {ing['protein']:.1f}g  "
                    f"🌾 C {ing['carbs']:.1f}g  "
                    f"🥑 F {ing['fat']:.1f}g"
                    + (f"  ⚖️ {ing['portion_g']:.0f}g" if ing.get("portion_g") else ""),
                )

        st.divider()


def diary_page():
    st.markdown(
        "<h2 style='color:#E8EAED; margin-bottom:4px;'>📋 Food Diary</h2>"
        "<p style='color:#8B8FA8; margin-bottom:20px;'>"
        "Your meals for the day.</p>",
        unsafe_allow_html=True,
    )

    user_id = st.session_state.get("user_id", "guest")
    goals = st.session_state.get("goals", {})

    # ── Date picker ───────────────────────────────────────────
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_date = st.date_input(
            "Date",
            value=date.today(),
            max_value=date.today(),
            label_visibility="collapsed",
        )
    with col2:
        if st.button("📅 Today", use_container_width=True):
            st.rerun()

    # ── Fetch meals (grouped) ─────────────────────────────────
    meals = fetch_today_meals(user_id, for_date=selected_date)

    if not meals:
        st.markdown(
            """
            <div style='text-align:center; padding:40px; color:#8B8FA8;'>
                <div style='font-size:48px;'>🍽️</div>
                <p>No meals logged for this day.</p>
                <p style='font-size:13px;'>
                    Go to <b>Analyse</b> to log your first meal!
                </p>
            </div>
        """,
            unsafe_allow_html=True,
        )
        return

    # ── Daily summary ─────────────────────────────────────────
    total_cal = sum(m["total_calories"] for m in meals)
    total_protein = sum(m["total_protein"] for m in meals)
    total_carbs = sum(m["total_carbs"] for m in meals)
    total_fat = sum(m["total_fat"] for m in meals)
    cal_goal = goals.get("calories", 2000)

    st.markdown(
        "<p style='color:#8B8FA8; font-size:13px; margin: 0 0 6px 0;'>"
        "Daily Summary</p>",
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "🔥 Calories", f"{total_cal:.0f}", delta=f"{cal_goal - total_cal:.0f} left"
        )
    with col2:
        st.metric("💪 Protein", f"{total_protein:.1f}g")
    with col3:
        st.metric("🌾 Carbs", f"{total_carbs:.1f}g")
    with col4:
        st.metric("🥑 Fat", f"{total_fat:.1f}g")

    st.progress(min(total_cal / cal_goal if cal_goal > 0 else 0, 1.0))
    st.caption(f"{total_cal:.0f} / {cal_goal} kcal  —  {len(meals)} meal(s) logged")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Meal cards ────────────────────────────────────────────
    st.markdown(
        f"<p style='color:#8B8FA8; font-size:13px; margin-bottom:8px;'>"
        f"{len(meals)} meal(s)</p>",
        unsafe_allow_html=True,
    )

    for meal in meals:
        render_meal_card(meal)


diary_page()
