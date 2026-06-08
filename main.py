import streamlit as st
from dotenv import load_dotenv
from db import get_user, create_user, fetch_goals, fetch_streak

load_dotenv()

st.set_page_config(
    page_title="NutriLens AI",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .stApp {
        background-color: #0F1117;
        color: #E8EAED;
    }
    [data-testid="stSidebar"] {
        background-color: #1A1D27;
        border-right: 1px solid #2E3147;
    }
    .nutricard {
        background-color: #1A1D27;
        border: 1px solid #2E3147;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    [data-testid="stMetricLabel"] {
        color: #8B8FA8 !important;
        font-size: 12px !important;
    }
    [data-testid="stMetricValue"] {
        color: #E8EAED !important;
        font-size: 24px !important;
        font-weight: 700 !important;
    }
    .badge-veg {
        background-color: #1A3A2A;
        color: #43e97b;
        border: 1px solid #43e97b;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-nonveg {
        background-color: #3A1A1A;
        color: #FF6B6B;
        border: 1px solid #FF6B6B;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-flagged {
        background-color: #3A2A1A;
        color: #FFB347;
        border: 1px solid #FFB347;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 12px;
        font-weight: 600;
    }
    .stProgress > div > div {
        background-color: #6C63FF;
    }
    #MainMenu  { visibility: hidden; }
    footer     { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)


def init_session():
    if st.session_state.get("initialized"):
        return

    user_id = "guest"
    user = get_user(user_id)
    if not user:
        user = create_user(user_id, name="Guest")

    goals = fetch_goals(user_id)
    streak = fetch_streak(user_id)

    # Load today's totals on startup
    from db import fetch_daily_total

    daily = fetch_daily_total(user_id)

    st.session_state.user_id = user_id
    st.session_state.user_name = user["name"]
    st.session_state.goals = goals
    st.session_state.diet_preference = user.get("diet_preference", "both")
    st.session_state.streak = streak["current"]
    st.session_state.longest_streak = streak["longest"]
    st.session_state.badge_3 = streak["badge_3"]
    st.session_state.badge_7 = streak["badge_7"]
    st.session_state.badge_14 = streak["badge_14"]
    st.session_state.badge_30 = streak["badge_30"]
    st.session_state.today_calories = daily.get("total_calories", 0) or 0
    st.session_state.today_protein = daily.get("total_protein", 0) or 0
    st.session_state.today_carbs = daily.get("total_carbs", 0) or 0
    st.session_state.today_fat = daily.get("total_fat", 0) or 0
    st.session_state.initialized = True


def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style='text-align:center; padding: 16px 0 8px 0;'>
                <span style='font-size:40px;'>🥗</span>
                <h2 style='color:#E8EAED; margin:4px 0 0 0;'>NutriLens AI</h2>
                <p style='color:#8B8FA8; font-size:12px; margin:0;'>
                    AI-Powered Nutrition Tracker
                </p>
            </div>
            <hr style='border-color:#2E3147; margin: 12px 0;'>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<p style='color:#8B8FA8; font-size:13px; margin:0;'>Logged in as</p>"
            f"<p style='color:#E8EAED; font-weight:600; margin:0 0 12px 0;'>"
            f"{st.session_state.get('user_name', 'Guest')}</p>",
            unsafe_allow_html=True,
        )

        preference = st.session_state.get("diet_preference", "both")
        if preference == "veg":
            badge = "<span class='badge-veg'>🟢 Vegetarian</span>"
        elif preference == "non_veg":
            badge = "<span class='badge-nonveg'>🔴 Non-Vegetarian</span>"
        else:
            badge = (
                "<span style='color:#8B8FA8; font-size:13px;'>🍽️ No preference</span>"
            )
        st.markdown(badge, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        streak = st.session_state.get("streak", 0)
        longest = st.session_state.get("longest_streak", 0)
        st.metric("🔥 Current Streak", f"{streak} day{'s' if streak != 1 else ''}")
        st.caption(f"Longest: {longest} days")

        badges = []
        if st.session_state.get("badge_3"):
            badges.append("🏅 3-day")
        if st.session_state.get("badge_7"):
            badges.append("🏅 7-day")
        if st.session_state.get("badge_14"):
            badges.append("🏅 14-day")
        if st.session_state.get("badge_30"):
            badges.append("🏅 30-day")
        if badges:
            st.markdown(
                "<p style='color:#8B8FA8; font-size:12px; margin: 8px 0 4px 0;'>Badges</p>"
                + " ".join(
                    f"<span style='margin-right:4px;'>{b}</span>" for b in badges
                ),
                unsafe_allow_html=True,
            )

        st.markdown(
            "<hr style='border-color:#2E3147; margin: 16px 0;'>", unsafe_allow_html=True
        )

        goals = st.session_state.get("goals", {})
        cal_goal = goals.get("calories", 2000)

        st.markdown(
            "<p style='color:#8B8FA8; font-size:12px; margin: 0 0 6px 0;'>"
            "Today's Progress</p>",
            unsafe_allow_html=True,
        )

        today_cal = st.session_state.get("today_calories", 0)
        today_protein = st.session_state.get("today_protein", 0)
        today_carbs = st.session_state.get("today_carbs", 0)
        today_fat = st.session_state.get("today_fat", 0)

        st.progress(min(today_cal / cal_goal if cal_goal > 0 else 0, 1.0))
        st.caption(f"🔥 {today_cal:.0f} / {cal_goal} kcal")
        st.caption(
            f"💪 {today_protein:.1f}g  🌾 {today_carbs:.1f}g  🥑 {today_fat:.1f}g"
        )


def main():
    init_session()

    # Define all pages
    pg = st.navigation(
        {
            "": [
                st.Page("pages/home.py", title="Home", icon="🏠"),
            ],
            "Tracking": [
                st.Page("pages/analyse.py", title="Analyse", icon="📸"),
                st.Page("pages/diary.py", title="Diary", icon="📋"),
                st.Page("pages/dashboard.py", title="Dashboard", icon="📊"),
            ],
            "Profile": [
                st.Page("pages/goals.py", title="Goals", icon="🎯"),
                st.Page("pages/settings.py", title="Settings", icon="⚙️"),
            ],
        },
        position="sidebar",
    )

    render_sidebar()

    pg.run()


if __name__ == "__main__":
    main()
