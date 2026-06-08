import streamlit as st
import json
import csv
import io
from datetime import date, timedelta
from db import get_user, fetch_logs_range
from db.connection import get_db
from db.queries import get_cursor


def update_user_name(user_id: str, name: str):
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("UPDATE users SET name = %s WHERE id = %s", (name, user_id))


def settings_page():
    st.markdown(
        "<h2 style='color:#E8EAED; margin-bottom:4px;'>⚙️ Settings</h2>"
        "<p style='color:#8B8FA8; margin-bottom:20px;'>"
        "Manage your profile and export your data.</p>",
        unsafe_allow_html=True,
    )

    user_id = st.session_state.get("user_id", "guest")
    user = get_user(user_id)

    # ── Profile ───────────────────────────────────────────────
    st.markdown(
        "<p style='color:#E8EAED; font-weight:600; margin-bottom:8px;'>Profile</p>",
        unsafe_allow_html=True,
    )

    with st.form("profile_form"):
        new_name = st.text_input("Display Name", value=user.get("name", "Guest"))
        new_email = st.text_input("Email (optional)", value=user.get("email") or "")
        new_units = st.radio(
            "Units",
            options=["metric", "imperial"],
            index=0 if user.get("units", "metric") == "metric" else 1,
            format_func=lambda x: (
                "📏 Metric (kg, g)" if x == "metric" else "📐 Imperial (lbs, oz)"
            ),
            horizontal=True,
        )

        if st.form_submit_button("💾 Save Profile", use_container_width=True):
            update_user_name(user_id, new_name)
            with get_db() as conn:
                with get_cursor(conn) as cur:
                    cur.execute(
                        "UPDATE users SET email = %s, units = %s WHERE id = %s",
                        (new_email or None, new_units, user_id),
                    )
            st.session_state.user_name = new_name
            st.success("✅ Profile updated!")
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Change Password ───────────────────────────────────────
    st.markdown(
        "<p style='color:#E8EAED; font-weight:600; margin-bottom:8px;'>"
        "Change Password</p>",
        unsafe_allow_html=True,
    )

    with st.form("change_password_form"):
        curr_pass = st.text_input("Current Password", type="password")
        new_pass = st.text_input("New Password", type="password")
        conf_pass = st.text_input("Confirm New", type="password")

        if st.form_submit_button("🔒 Update Password", use_container_width=True):
            from utils.auth import verify_password, hash_password
            from db.queries import update_password

            user = get_user(user_id)
            if not verify_password(curr_pass, user["password_hash"]):
                st.error("Current password is incorrect.")
            elif len(new_pass) < 6:
                st.error("New password must be at least 6 characters.")
            elif new_pass != conf_pass:
                st.error("Passwords do not match.")
            else:
                update_password(user_id, hash_password(new_pass))
                st.success("✅ Password updated successfully!")

    # ── Data Export ───────────────────────────────────────────
    st.markdown(
        "<p style='color:#E8EAED; font-weight:600; margin-bottom:8px;'>Export Data</p>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        export_days = st.selectbox(
            "Export range",
            options=[7, 14, 30, 90],
            format_func=lambda x: f"Last {x} days",
        )
    with col2:
        export_format = st.selectbox(
            "Format",
            options=["CSV", "JSON"],
        )

    if st.button("📥 Export", use_container_width=True):
        start = date.today() - timedelta(days=export_days)
        logs = fetch_logs_range(user_id, start, date.today())

        if not logs:
            st.warning("No data to export for this period.")
        else:
            if export_format == "CSV":
                buf = io.StringIO()
                writer = csv.DictWriter(
                    buf,
                    fieldnames=[
                        "id",
                        "logged_at",
                        "log_date",
                        "food_name",
                        "portion_g",
                        "calories",
                        "protein",
                        "carbs",
                        "fat",
                        "source",
                        "confidence",
                        "notes",
                    ],
                )
                writer.writeheader()
                for log in logs:
                    writer.writerow({k: log[k] for k in writer.fieldnames if k in log})
                st.download_button(
                    label="⬇️ Download CSV",
                    data=buf.getvalue(),
                    file_name=f"nutrilens_export_{date.today()}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                data = [dict(log) for log in logs]
                for row in data:
                    for k, v in row.items():
                        if hasattr(v, "isoformat"):
                            row[k] = v.isoformat()
                st.download_button(
                    label="⬇️ Download JSON",
                    data=json.dumps(data, indent=2),
                    file_name=f"nutrilens_export_{date.today()}.json",
                    mime="application/json",
                    use_container_width=True,
                )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── App info ──────────────────────────────────────────────
    st.markdown(
        "<p style='color:#E8EAED; font-weight:600; margin-bottom:8px;'>About</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class='nutricard'>
            <p style='color:#8B8FA8; font-size:13px; margin:0 0 6px 0;'>
                NutriLens AI — v1.0
            </p>
            <p style='color:#8B8FA8; font-size:12px; margin:0;'>
                Built with Streamlit · LangGraph · Groq · PostgreSQL
            </p>
            <p style='color:#8B8FA8; font-size:12px; margin:4px 0 0 0;'>
                User ID: <code style='color:#6C63FF;'>{user_id}</code>
            </p>
            <p style='color:#8B8FA8; font-size:12px; margin:4px 0 0 0;'>
                Member since: {str(user.get("created_at", ""))[:10]}
            </p>
        </div>
    """,
        unsafe_allow_html=True,
    )


settings_page()
