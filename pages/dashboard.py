import streamlit as st
import plotly.graph_objects as go
from db import fetch_daily_total, fetch_weekly_summary


def macro_ring_svg(label, value, goal, color, size=120):
    """Generate SVG progress ring for a macro."""
    pct = min(value / goal, 1.0) if goal > 0 else 0
    r = 44
    circ = 2 * 3.14159 * r
    dash = pct * circ
    remaining = max(goal - value, 0)

    return f"""
    <svg width="{size}" height="{size + 20}" viewBox="0 0 100 120"
         xmlns="http://www.w3.org/2000/svg">
        <!-- Background ring -->
        <circle cx="50" cy="50" r="{r}" fill="none"
                stroke="#2E3147" stroke-width="10"/>
        <!-- Progress ring -->
        <circle cx="50" cy="50" r="{r}" fill="none"
                stroke="{color}" stroke-width="10"
                stroke-dasharray="{dash:.1f} {circ:.1f}"
                stroke-linecap="round"
                transform="rotate(-90 50 50)"
                style="transition: stroke-dasharray 0.8s ease;"/>
        <!-- Value text -->
        <text x="50" y="46" text-anchor="middle"
              font-size="14" fill="white" font-weight="bold">
            {value:.0f}g
        </text>
        <!-- Label text -->
        <text x="50" y="62" text-anchor="middle"
              font-size="9" fill="#8B8FA8">{label}</text>
        <!-- Remaining text -->
        <text x="50" y="108" text-anchor="middle"
              font-size="9" fill="#8B8FA8">{remaining:.0f}g left</text>
    </svg>
    """


def render_macro_rings(daily_total, goals):
    """Render three macro progress rings side by side."""
    st.markdown(
        "<p style='color:#8B8FA8; font-size:13px; margin-bottom:12px;'>"
        "Today's Macro Progress</p>",
        unsafe_allow_html=True,
    )

    rings_html = f"""
    <div style='display:flex; justify-content:space-around;
                background:#1A1D27; border:1px solid #2E3147;
                border-radius:12px; padding:20px;'>
        {
        macro_ring_svg(
            "Protein",
            daily_total.get("total_protein", 0),
            goals.get("protein", 150),
            "#6C63FF",
        )
    }
        {
        macro_ring_svg(
            "Carbs",
            daily_total.get("total_carbs", 0),
            goals.get("carbs", 200),
            "#00D4AA",
        )
    }
        {
        macro_ring_svg(
            "Fat", daily_total.get("total_fat", 0), goals.get("fat", 65), "#FF6B6B"
        )
    }
    </div>
    """
    st.components.v1.html(rings_html, height=160)


def render_weekly_chart(weekly_data, goals, selected_macro):
    """Render Plotly weekly bar chart for selected macro."""
    if not weekly_data:
        st.info("No data yet for the past 7 days.")
        return

    dates = [str(row["log_date"]) for row in weekly_data]
    macro_map = {
        "Calories": ("total_calories", "#6C63FF", goals.get("calories", 2000)),
        "Protein": ("total_protein", "#00D4AA", goals.get("protein", 150)),
        "Carbs": ("total_carbs", "#FFB347", goals.get("carbs", 200)),
        "Fat": ("total_fat", "#FF6B6B", goals.get("fat", 65)),
    }

    key, color, goal_val = macro_map[selected_macro]
    values = [float(row.get(key, 0) or 0) for row in weekly_data]
    unit = "kcal" if selected_macro == "Calories" else "g"

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=dates,
            y=values,
            marker_color=color,
            marker_line_width=0,
            name=selected_macro,
            hovertemplate=f"%{{x}}<br>{selected_macro}: %{{y:.0f}}{unit}<extra></extra>",
        )
    )
    fig.add_hline(
        y=goal_val,
        line_dash="dash",
        line_color="#8B8FA8",
        annotation_text=f"Goal: {goal_val}{unit}",
        annotation_font_color="#8B8FA8",
    )
    fig.update_layout(
        paper_bgcolor="#0F1117",
        plot_bgcolor="#1A1D27",
        font=dict(color="#E8EAED"),
        margin=dict(l=0, r=0, t=10, b=0),
        showlegend=False,
        height=280,
        xaxis=dict(gridcolor="#2E3147"),
        yaxis=dict(gridcolor="#2E3147"),
    )
    st.plotly_chart(fig, use_container_width=True)


def dashboard_page():
    st.markdown(
        "<h2 style='color:#E8EAED; margin-bottom:4px;'>📊 Dashboard</h2>"
        "<p style='color:#8B8FA8; margin-bottom:20px;'>"
        "Your nutrition overview at a glance.</p>",
        unsafe_allow_html=True,
    )

    user_id = st.session_state.get("user_id", "guest")
    goals = st.session_state.get("goals", {})

    # ── Today's totals ────────────────────────────────────────
    daily_total = fetch_daily_total(user_id)
    cal_goal = goals.get("calories", 2000)
    total_cal = daily_total.get("total_calories", 0) or 0

    # Calorie summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class='nutricard' style='text-align:center;'>
                <p style='color:#8B8FA8; font-size:12px; margin:0;'>Consumed</p>
                <p style='color:#FF6B6B; font-size:28px;
                          font-weight:700; margin:4px 0;'>
                    {total_cal:.0f}
                </p>
                <p style='color:#8B8FA8; font-size:12px; margin:0;'>kcal</p>
            </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class='nutricard' style='text-align:center;'>
                <p style='color:#8B8FA8; font-size:12px; margin:0;'>Remaining</p>
                <p style='color:#43e97b; font-size:28px;
                          font-weight:700; margin:4px 0;'>
                    {max(cal_goal - total_cal, 0):.0f}
                </p>
                <p style='color:#8B8FA8; font-size:12px; margin:0;'>kcal</p>
            </div>
        """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class='nutricard' style='text-align:center;'>
                <p style='color:#8B8FA8; font-size:12px; margin:0;'>Goal</p>
                <p style='color:#6C63FF; font-size:28px;
                          font-weight:700; margin:4px 0;'>
                    {cal_goal}
                </p>
                <p style='color:#8B8FA8; font-size:12px; margin:0;'>kcal</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

    st.progress(min(total_cal / cal_goal if cal_goal > 0 else 0, 1.0))
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Macro rings ───────────────────────────────────────────
    render_macro_rings(daily_total, goals)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Weekly chart ──────────────────────────────────────────
    st.markdown(
        "<p style='color:#8B8FA8; font-size:13px; margin-bottom:8px;'>"
        "Weekly History</p>",
        unsafe_allow_html=True,
    )

    weekly_data = fetch_weekly_summary(user_id)
    selected_macro = st.radio(
        "Macro",
        ["Calories", "Protein", "Carbs", "Fat"],
        horizontal=True,
        label_visibility="collapsed",
    )
    render_weekly_chart(weekly_data, goals, selected_macro)

    # ── Streak card ───────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    streak = st.session_state.get("streak", 0)
    longest = st.session_state.get("longest_streak", 0)

    st.markdown(
        f"""
        <div class='nutricard' style='text-align:center;'>
            <div style='font-size:40px;'>🔥</div>
            <h3 style='color:#E8EAED; margin:8px 0 4px 0;'>
                {streak} Day Streak
            </h3>
            <p style='color:#8B8FA8; font-size:13px; margin:0;'>
                Longest: {longest} days
            </p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Badges
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
            "<div style='text-align:center; margin-top:8px;'>"
            + "  ".join(
                f"<span style='background:#1A1D27; border:1px solid #2E3147;"
                f"border-radius:20px; padding:4px 12px; font-size:13px;'>{b}</span>"
                for b in badges
            )
            + "</div>",
            unsafe_allow_html=True,
        )


dashboard_page()
