# utils/auth.py
import uuid
import bcrypt
import streamlit as st
from db.queries import (
    get_user,
    get_user_by_email,
    create_user_with_password,
    fetch_goals,
    fetch_streak,
    fetch_daily_total,
)


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a plain text password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def load_user_into_session(user: dict):
    """
    Hydrate session state from a user row.
    Called after successful login or registration.
    """
    user_id = user["id"]
    goals = fetch_goals(user_id)
    streak = fetch_streak(user_id)
    daily = fetch_daily_total(user_id)

    st.session_state.user_id = user_id
    st.session_state.user_name = user["name"]
    st.session_state.user_email = user.get("email", "")
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
    st.session_state.authenticated = True
    st.session_state.initialized = True


def login(email: str, password: str) -> tuple[bool, str]:
    """
    Attempt login with email + password.
    Returns (success, message).
    """
    if not email or not password:
        return False, "Please enter email and password."

    user = get_user_by_email(email.strip().lower())
    if not user:
        return False, "No account found with that email."

    if not user.get("password_hash"):
        return False, "Account has no password set."

    if not verify_password(password, user["password_hash"]):
        return False, "Incorrect password."

    load_user_into_session(user)
    return True, f"Welcome back, {user['name']}!"


def register(name: str, email: str, password: str, confirm: str) -> tuple[bool, str]:
    """
    Register a new user.
    Returns (success, message).
    """
    if not all([name, email, password, confirm]):
        return False, "All fields are required."

    if len(name.strip()) < 2:
        return False, "Name must be at least 2 characters."

    if "@" not in email or "." not in email:
        return False, "Please enter a valid email address."

    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    if password != confirm:
        return False, "Passwords do not match."

    # Check if email already registered
    existing = get_user_by_email(email.strip().lower())
    if existing:
        return False, "An account with this email already exists."

    # Create user
    user_id = str(uuid.uuid4())
    hashed = hash_password(password)
    user = create_user_with_password(
        user_id=user_id,
        name=name.strip(),
        email=email.strip().lower(),
        password_hash=hashed,
    )

    load_user_into_session(user)
    return True, f"Account created! Welcome, {name.strip()}!"


def logout():
    """Clear all session state and log out."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def is_authenticated() -> bool:
    """Check if current session is authenticated."""
    return st.session_state.get("authenticated", False)
