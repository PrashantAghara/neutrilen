import streamlit as st


def render_home():
    st.markdown(
        """
        <div style='text-align:center; padding: 40px 0 20px 0;'>
            <span style='font-size:64px;'>🥗</span>
            <h1 style='color:#E8EAED; margin: 16px 0 8px 0;'>NutriLens AI</h1>
            <p style='color:#8B8FA8; font-size:16px; max-width:500px; margin:0 auto;'>
                AI-powered nutrition tracking. Snap a photo of your meal
                and get an instant macro breakdown.
            </p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            <div class='nutricard' style='text-align:center;'>
                <div style='font-size:32px;'>📸</div>
                <h3 style='color:#E8EAED; margin:8px 0 4px 0;'>Snap & Analyse</h3>
                <p style='color:#8B8FA8; font-size:13px; margin:0;'>
                    Upload or take a photo of any meal.
                    Get instant ingredient-level macro breakdown.
                </p>
            </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class='nutricard' style='text-align:center;'>
                <div style='font-size:32px;'>📊</div>
                <h3 style='color:#E8EAED; margin:8px 0 4px 0;'>Track Daily</h3>
                <p style='color:#8B8FA8; font-size:13px; margin:0;'>
                    Monitor calories, protein, carbs, and fat
                    against your personal goals.
                </p>
            </div>
        """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class='nutricard' style='text-align:center;'>
                <div style='font-size:32px;'>🔥</div>
                <h3 style='color:#E8EAED; margin:8px 0 4px 0;'>Build Streaks</h3>
                <p style='color:#8B8FA8; font-size:13px; margin:0;'>
                    Log every day to build your streak
                    and earn milestone badges.
                </p>
            </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    goals = st.session_state.get("goals", {})
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎯 Calorie Goal", f"{goals.get('calories', 2000)} kcal")
    with col2:
        st.metric("💪 Protein Goal", f"{goals.get('protein', 150)}g")
    with col3:
        st.metric("🌾 Carbs Goal", f"{goals.get('carbs', 200)}g")
    with col4:
        st.metric("🥑 Fat Goal", f"{goals.get('fat', 65)}g")

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("👈 Use the sidebar to navigate to **Analyse** to log your first meal.")


render_home()
