import streamlit as st
import io
from PIL import Image
from utils.image_utils import bytes_to_b64, md5_hash
from db import get_cached_image, fetch_goals
from agents import nutrilens_graph, AgentState


def render_macro_card(entries, dish_name, cuisine, daily_total, advice):

    # Dish header
    st.markdown(
        f"""
        <div style='background:#1A1D27; border:1px solid #2E3147;
                    border-radius:12px; padding:16px; margin-bottom:12px;'>
            <h3 style='color:#E8EAED; margin:0 0 4px 0;'>{dish_name}</h3>
            <span style='color:#8B8FA8; font-size:13px;'>{cuisine}</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Ingredient breakdown
    st.markdown(
        "<p style='color:#8B8FA8; font-size:13px; margin: 12px 0 6px 0;'>"
        "Ingredient Breakdown</p>",
        unsafe_allow_html=True,
    )

    for entry in entries:
        veg_icon = "🟢" if entry.is_veg else "🔴"
        conf_color = (
            "green"
            if entry.confidence >= 0.8
            else "orange"
            if entry.confidence >= 0.6
            else "red"
        )

        with st.container():
            col_name, col_conf = st.columns([3, 1])

            with col_name:
                flag = " ⚠️ Non-veg detected" if entry.flagged else ""
                st.markdown(f"**{veg_icon} {entry.food_name}**{flag}")
            with col_conf:
                st.markdown(
                    f"<span style='color:{conf_color}; font-size:12px;'>"
                    f"{entry.confidence * 100:.0f}% conf</span>",
                    unsafe_allow_html=True,
                )

            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("🔥 kcal", f"{entry.calories:.0f}")
            with col2:
                st.metric("💪 Protein", f"{entry.protein:.1f}g")
            with col3:
                st.metric("🌾 Carbs", f"{entry.carbs:.1f}g")
            with col4:
                st.metric("🥑 Fat", f"{entry.fat:.1f}g")
            with col5:
                if entry.portion_g:
                    st.metric("⚖️ Portion", f"{entry.portion_g:.0f}g")

            st.divider()

    # Daily total summary
    st.markdown(
        "<p style='color:#8B8FA8; font-size:13px; margin: 8px 0 6px 0;'>"
        "Today's Running Total</p>",
        unsafe_allow_html=True,
    )

    goals = st.session_state.get("goals", {})
    cal_goal = goals.get("calories", 2000)
    total_cal = daily_total.get("total_calories", 0)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "🔥 Calories", f"{total_cal:.0f}", delta=f"{cal_goal - total_cal:.0f} left"
        )
    with col2:
        st.metric("💪 Protein", f"{daily_total.get('total_protein', 0):.1f}g")
    with col3:
        st.metric("🌾 Carbs", f"{daily_total.get('total_carbs', 0):.1f}g")
    with col4:
        st.metric("🥑 Fat", f"{daily_total.get('total_fat', 0):.1f}g")

    st.progress(min(total_cal / cal_goal if cal_goal > 0 else 0, 1.0))
    st.caption(f"{total_cal:.0f} / {cal_goal} kcal consumed today")

    # AI Advice
    if advice:
        st.info(f"🤖 **AI Nutrition Advice**\n\n{advice}")


def analyse_page():
    st.markdown(
        "<h2 style='color:#E8EAED; margin-bottom:4px;'>📸 Analyse Meal</h2>"
        "<p style='color:#8B8FA8; margin-bottom:20px;'>"
        "Upload a photo or use your camera to get an instant macro breakdown.</p>",
        unsafe_allow_html=True,
    )

    # ── Upload / Camera tabs ──────────────────────────────────
    tab_upload, tab_camera = st.tabs(["📁 Upload Photo", "📷 Camera"])

    image_b64 = None
    image_bytes = None

    with tab_upload:
        uploaded = st.file_uploader(
            "Choose a food photo",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="collapsed",
        )
        if uploaded:
            image_bytes = uploaded.read()
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            st.image(img, caption="Uploaded image", use_container_width=True)
            image_b64 = bytes_to_b64(image_bytes)

    with tab_camera:
        camera_img = st.camera_input("Take a photo of your meal")
        if camera_img:
            image_bytes = camera_img.getvalue()
            image_b64 = bytes_to_b64(image_bytes)

    # ── Analyse Button ────────────────────────────────────────
    if image_b64:
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🔍 Analyse Meal", type="primary", use_container_width=True):
            # Check image cache first
            h = md5_hash(image_bytes)
            cached = get_cached_image(h)

            if cached:
                st.success("⚡ Instant result from cache!")
                st.markdown(
                    f"""
                    <div class='nutricard'>
                        <p style='color:#E8EAED; font-weight:600; margin:0;'>
                            {cached["food_name"]}
                        </p>
                        <div style='display:flex; gap:16px; margin-top:8px;'>
                            <span style='color:#FF6B6B;'>
                                🔥 {cached["calories"]:.0f} kcal
                            </span>
                            <span style='color:#6C63FF;'>
                                💪 P {cached["protein"]:.1f}g
                            </span>
                            <span style='color:#00D4AA;'>
                                🌾 C {cached["carbs"]:.1f}g
                            </span>
                            <span style='color:#FFB347;'>
                                🥑 F {cached["fat"]:.1f}g
                            </span>
                        </div>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

            else:
                # Run full LangGraph pipeline
                with st.spinner("🤖 Analysing your meal with AI..."):
                    initial_state: AgentState = {
                        "user_id": st.session_state.get("user_id", "guest"),
                        "image_b64": image_b64,
                        "dish_name": "",
                        "cuisine": "",
                        "diet_preference": st.session_state.get(
                            "diet_preference", "both"
                        ),
                        "raw_vision_text": "",
                        "nutrition_entries": [],
                        "daily_total": {},
                        "goals": st.session_state.get("goals", fetch_goals("guest")),
                        "streak": st.session_state.get("streak", 0),
                        "advice": "",
                        "error": None,
                    }

                    result = nutrilens_graph.invoke(initial_state)

                if result.get("error"):
                    st.error(f"Analysis failed: {result['error']}")
                else:
                    # Sync session state after every analyse run
                    st.session_state.streak = result["streak"]
                    st.session_state.today_calories = result["daily_total"].get(
                        "total_calories", 0
                    )
                    st.session_state.today_protein = result["daily_total"].get(
                        "total_protein", 0
                    )
                    st.session_state.today_carbs = result["daily_total"].get(
                        "total_carbs", 0
                    )
                    st.session_state.today_fat = result["daily_total"].get(
                        "total_fat", 0
                    )

                    # Update badges in session state
                    streak = result["streak"]
                    if streak >= 3:
                        st.session_state.badge_3 = True
                    if streak >= 7:
                        st.session_state.badge_7 = True
                    if streak >= 14:
                        st.session_state.badge_14 = True
                    if streak >= 30:
                        st.session_state.badge_30 = True

                    # Balloons only on milestone days exactly
                    if streak in [3, 7, 14, 30]:
                        st.balloons()
                        st.success(f"🏅 {streak}-day streak milestone reached!")

                    flagged = [
                        e.food_name for e in result["nutrition_entries"] if e.flagged
                    ]
                    if flagged:
                        st.warning(
                            f"⚠️ Non-veg items detected for vegetarian profile: "
                            f"{', '.join(flagged)}"
                        )

                    st.success("✅ Analysis complete!")
                    render_macro_card(
                        entries=result["nutrition_entries"],
                        dish_name=result["dish_name"],
                        cuisine=result["cuisine"],
                        daily_total=result["daily_total"],
                        advice=result["advice"],
                    )


analyse_page()
