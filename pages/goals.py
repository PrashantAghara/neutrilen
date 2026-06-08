import streamlit as st
from db import update_user_goals, get_user
from db.connection import get_db
from db.queries import get_cursor


def update_diet_preference(user_id: str, preference: str):
    """Update diet preference in DB."""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute(
                "UPDATE users SET diet_preference = %s WHERE id = %s",
                (preference, user_id),
            )


def goals_page():
    st.markdown(
        "<h2 style='color:#E8EAED; margin-bottom:4px;'>🎯 Goals & Preferences</h2>"
        "<p style='color:#8B8FA8; margin-bottom:20px;'>"
        "Set your daily nutrition targets and diet preference.</p>",
        unsafe_allow_html=True,
    )

    user_id = st.session_state.get("user_id", "guest")
    goals = st.session_state.get("goals", {})

    # ── Diet type ─────────────────────────────────────────────
    st.markdown(
        "<p style='color:#E8EAED; font-weight:600; margin-bottom:8px;'>Diet Type</p>",
        unsafe_allow_html=True,
    )
    diet_type = st.radio(
        "Diet type",
        options=["maintain", "cut", "bulk"],
        index=["maintain", "cut", "bulk"].index(
            get_user(user_id).get("diet_type", "maintain")
        ),
        format_func=lambda x: {
            "maintain": "⚖️  Maintain — keep current weight",
            "cut": "📉  Cut — lose fat",
            "bulk": "📈  Bulk — build muscle",
        }[x],
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Diet preference ───────────────────────────────────────
    st.markdown(
        "<p style='color:#E8EAED; font-weight:600; margin-bottom:8px;'>"
        "Diet Preference</p>",
        unsafe_allow_html=True,
    )
    current_pref = st.session_state.get("diet_preference", "both")
    preference = st.radio(
        "Diet preference",
        options=["veg", "non_veg", "both"],
        index=["veg", "non_veg", "both"].index(current_pref),
        format_func=lambda x: {
            "veg": "🟢  Vegetarian",
            "non_veg": "🔴  Non-Vegetarian",
            "both": "🍽️   No preference",
        }[x],
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Macro goals ───────────────────────────────────────────
    st.markdown(
        "<p style='color:#E8EAED; font-weight:600; margin-bottom:8px;'>"
        "Daily Targets</p>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        cal_goal = st.number_input(
            "🔥 Calories (kcal)",
            min_value=500,
            max_value=5000,
            step=50,
            value=int(goals.get("calories", 2000)),
        )
        protein_goal = st.number_input(
            "💪 Protein (g)",
            min_value=10,
            max_value=400,
            step=5,
            value=int(goals.get("protein", 150)),
        )
    with col2:
        carbs_goal = st.number_input(
            "🌾 Carbs (g)",
            min_value=10,
            max_value=600,
            step=5,
            value=int(goals.get("carbs", 200)),
        )
        fat_goal = st.number_input(
            "🥑 Fat (g)",
            min_value=10,
            max_value=200,
            step=5,
            value=int(goals.get("fat", 65)),
        )

    # Macro split preview
    total_macro_cal = (protein_goal * 4) + (carbs_goal * 4) + (fat_goal * 9)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#8B8FA8; font-size:13px; margin-bottom:6px;'>"
        "Macro Calorie Split Preview</p>",
        unsafe_allow_html=True,
    )

    if total_macro_cal > 0:
        p_pct = (protein_goal * 4) / total_macro_cal * 100
        c_pct = (carbs_goal * 4) / total_macro_cal * 100
        f_pct = (fat_goal * 9) / total_macro_cal * 100
        st.markdown(
            f"""
            <div style='background:#1A1D27; border:1px solid #2E3147;
                        border-radius:10px; padding:12px;'>
                <div style='display:flex; justify-content:space-between;
                            margin-bottom:8px;'>
                    <span style='color:#6C63FF; font-size:13px;'>
                        💪 Protein {p_pct:.0f}%
                    </span>
                    <span style='color:#00D4AA; font-size:13px;'>
                        🌾 Carbs {c_pct:.0f}%
                    </span>
                    <span style='color:#FF6B6B; font-size:13px;'>
                        🥑 Fat {f_pct:.0f}%
                    </span>
                </div>
                <div style='height:8px; border-radius:4px; overflow:hidden;
                            display:flex;'>
                    <div style='width:{p_pct:.0f}%; background:#6C63FF;'></div>
                    <div style='width:{c_pct:.0f}%; background:#00D4AA;'></div>
                    <div style='width:{f_pct:.0f}%; background:#FF6B6B;'></div>
                </div>
                <p style='color:#8B8FA8; font-size:12px; margin:8px 0 0 0;'>
                    Total from macros: {total_macro_cal} kcal
                    {"⚠️ Differs from calorie goal" if abs(total_macro_cal - cal_goal) > 100 else "✅"}
                </p>
            </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Save button ───────────────────────────────────────────
    if st.button("💾 Save Goals", type="primary", use_container_width=True):
        update_user_goals(
            user_id=user_id,
            cal_goal=cal_goal,
            protein_g=protein_goal,
            carbs_g=carbs_goal,
            fat_g=fat_goal,
            diet_type=diet_type,
        )
        update_diet_preference(user_id, preference)

        # Update session state
        st.session_state.goals = {
            "calories": cal_goal,
            "protein": protein_goal,
            "carbs": carbs_goal,
            "fat": fat_goal,
        }
        st.session_state.diet_preference = preference

        st.success("✅ Goals saved successfully!")
        st.rerun()


goals_page()
