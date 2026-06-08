# pages/0_Auth.py
import streamlit as st
from utils.auth import login, register


def auth_page():
    # Center the auth card
    _, col, _ = st.columns([1, 2, 1])

    with col:
        st.markdown(
            """
            <div style='text-align:center; padding: 32px 0 24px 0;'>
                <span style='font-size:56px;'>🥗</span>
                <h1 style='color:#E8EAED; margin:12px 0 4px 0;'>NutriLens AI</h1>
                <p style='color:#8B8FA8; font-size:14px; margin:0;'>
                    AI-Powered Nutrition Tracker
                </p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])

        # ── Login ─────────────────────────────────────────────
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)

            email = st.text_input(
                "Email", placeholder="you@example.com", key="login_email"
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Your password",
                key="login_password",
            )

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Login", type="primary", use_container_width=True):
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    with st.spinner("Logging in..."):
                        success, msg = login(email, password)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        # ── Register ──────────────────────────────────────────
        with tab_register:
            st.markdown("<br>", unsafe_allow_html=True)

            reg_name = st.text_input(
                "Full Name", placeholder="John Doe", key="reg_name"
            )
            reg_email = st.text_input(
                "Email", placeholder="you@example.com", key="reg_email"
            )
            reg_password = st.text_input(
                "Password",
                type="password",
                placeholder="Min 6 characters",
                key="reg_password",
            )
            reg_confirm = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Repeat password",
                key="reg_confirm",
            )

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Create Account", type="primary", use_container_width=True):
                with st.spinner("Creating account..."):
                    success, msg = register(
                        reg_name, reg_email, reg_password, reg_confirm
                    )
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        st.markdown(
            """
            <p style='text-align:center; color:#8B8FA8;
                    font-size:12px; margin-top:24px;'>
                Your data is private and stored securely.
            </p>
        """,
            unsafe_allow_html=True,
        )


auth_page()
