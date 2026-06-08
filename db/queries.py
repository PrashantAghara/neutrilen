from __future__ import annotations
import hashlib
from datetime import date
from typing import Optional
from db.connection import get_db, get_cursor

UserRow = dict
FoodLogRow = dict
StreakRow = dict
ImageCacheRow = dict
DailyTotalRow = dict


def get_user(user_id: str) -> Optional[UserRow]:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return cur.fetchone()


def create_user(
    user_id: str,
    name: str,
    email: Optional[str] = None,
    cal_goal: int = 2000,
    protein_g: int = 150,
    carbs_g: int = 200,
    fat_g: int = 65,
    diet_type: str = "maintain",
    units: str = "metric",
) -> UserRow:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute(
                """
                INSERT INTO users
                    (id, name, email, cal_goal, protein_g, carbs_g, fat_g, diet_type, units)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                RETURNING *
                """,
                (
                    user_id,
                    name,
                    email,
                    cal_goal,
                    protein_g,
                    carbs_g,
                    fat_g,
                    diet_type,
                    units,
                ),
            )
            row = cur.fetchone()
            if row is None:
                cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                row = cur.fetchone()
            return row


def update_user_goals(
    user_id: str,
    cal_goal: int,
    protein_g: int,
    carbs_g: int,
    fat_g: int,
    diet_type: str,
) -> UserRow:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute(
                """
                UPDATE users
                SET cal_goal  = %s,
                    protein_g = %s,
                    carbs_g   = %s,
                    fat_g     = %s,
                    diet_type = %s
                WHERE id = %s
                RETURNING *
                """,
                (cal_goal, protein_g, carbs_g, fat_g, diet_type, user_id),
            )
            return cur.fetchone()


def fetch_goals(user_id: str) -> dict:
    user = get_user(user_id)
    if not user:
        return {"calories": 2000, "protein": 150, "carbs": 200, "fat": 65}
    return {
        "calories": user["cal_goal"],
        "protein": user["protein_g"],
        "carbs": user["carbs_g"],
        "fat": user["fat_g"],
    }


def save_food_log(
    user_id: str,
    food_name: str,
    calories: float,
    protein: float,
    carbs: float,
    fat: float,
    portion_g: Optional[float] = None,
    image_b64: Optional[str] = None,
    confidence: float = 1.0,
    source: str = "groq",
    notes: Optional[str] = None,
) -> FoodLogRow:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute(
                """
                INSERT INTO food_logs
                    (user_id, food_name, calories, protein, carbs, fat, portion_g, image_b64, confidence, source, notes)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    user_id,
                    food_name,
                    calories,
                    protein,
                    carbs,
                    fat,
                    portion_g,
                    image_b64,
                    confidence,
                    source,
                    notes,
                ),
            )
            return cur.fetchone()


def save_food_logs_bulk(entries: list[dict]) -> list[FoodLogRow]:
    rows = []
    with get_db() as conn:
        with get_cursor(conn) as cur:
            for e in entries:
                cur.execute(
                    """
                    INSERT INTO food_logs
                        (user_id, meal_id, dish_name, food_name, calories,
                        protein, carbs, fat, portion_g, image_b64,
                        confidence, source, notes, is_veg, flagged)
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        e["user_id"],
                        e.get("meal_id"),
                        e.get("dish_name"),
                        e["food_name"],
                        e["calories"],
                        e["protein"],
                        e["carbs"],
                        e["fat"],
                        e.get("portion_g"),
                        e.get("image_b64"),
                        e.get("confidence", 1.0),
                        e.get("source", "groq"),
                        e.get("notes"),
                        e.get("is_veg", True),
                        e.get("flagged", False),
                    ),
                )
                rows.append(cur.fetchone())
    return rows


def fetch_today_logs(user_id: str, for_date: Optional[date] = None) -> list[FoodLogRow]:
    target = for_date or date.today()
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute(
                """
                SELECT * FROM food_logs
                WHERE user_id = %s AND log_date = %s
                ORDER BY logged_at ASC
                """,
                (user_id, target),
            )
            return cur.fetchall()


def fetch_logs_range(
    user_id: str,
    start_date: date,
    end_date: date,
) -> list[FoodLogRow]:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute(
                """
                SELECT * FROM food_logs
                WHERE user_id  = %s AND log_date >= %s AND log_date <= %s
                ORDER BY logged_at ASC
                """,
                (user_id, start_date, end_date),
            )
            return cur.fetchall()


def update_food_log(
    log_id: int,
    portion_g: float,
    calories: float,
    protein: float,
    carbs: float,
    fat: float,
    notes: Optional[str] = None,
) -> FoodLogRow:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute(
                """
                UPDATE food_logs
                SET portion_g = %s,
                    calories  = %s,
                    protein   = %s,
                    carbs     = %s,
                    fat       = %s,
                    notes     = %s
                WHERE id = %s
                RETURNING *
                """,
                (portion_g, calories, protein, carbs, fat, notes, log_id),
            )
            return cur.fetchone()


def delete_food_log(log_id: int) -> bool:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("DELETE FROM food_logs WHERE id = %s", (log_id,))
            return cur.rowcount > 0


def fetch_daily_total(user_id: str, for_date: Optional[date] = None) -> DailyTotalRow:
    target = for_date or date.today()
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute(
                """
                SELECT * FROM daily_totals
                WHERE user_id  = %s AND log_date = %s
                """,
                (user_id, target),
            )
            row = cur.fetchone()
            if row:
                return row
            # No logs yet — return zeros
            return {
                "user_id": user_id,
                "log_date": target,
                "total_calories": 0.0,
                "total_protein": 0.0,
                "total_carbs": 0.0,
                "total_fat": 0.0,
                "meal_count": 0,
            }


def fetch_weekly_summary(user_id: str) -> list[DailyTotalRow]:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute(
                """
                SELECT * FROM weekly_summary
                WHERE user_id = %s
                ORDER BY log_date ASC
                """,
                (user_id,),
            )
            return cur.fetchall()


def fetch_streak(user_id: str) -> StreakRow:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT * FROM streaks WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            if row:
                return row
            cur.execute(
                """
                INSERT INTO streaks (user_id)
                VALUES (%s)
                ON CONFLICT (user_id) DO NOTHING
                RETURNING *
                """,
                (user_id,),
            )
            return cur.fetchone()


def update_streak(user_id: str) -> StreakRow:
    today = date.today()
    yesterday = date.fromordinal(today.toordinal() - 1)
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute(
                "SELECT * FROM streaks WHERE user_id = %s FOR UPDATE", (user_id,)
            )
            row = cur.fetchone()

            if not row:
                cur.execute(
                    "INSERT INTO streaks (user_id) VALUES (%s) RETURNING *", (user_id,)
                )
                row = cur.fetchone()

            last_log = row["last_log"]

            if last_log == today:
                return row

            if last_log == yesterday:
                new_current = row["current"] + 1
            else:
                new_current = 1

            new_longest = max(row["longest"], new_current)

            badge_3 = row["badge_3"] or new_current >= 3
            badge_7 = row["badge_7"] or new_current >= 7
            badge_14 = row["badge_14"] or new_current >= 14
            badge_30 = row["badge_30"] or new_current >= 30

            cur.execute(
                """
                UPDATE streaks
                SET current  = %s,
                    longest  = %s,
                    last_log = %s,
                    badge_3  = %s,
                    badge_7  = %s,
                    badge_14 = %s,
                    badge_30 = %s
                WHERE user_id = %s
                RETURNING *
                """,
                (
                    new_current,
                    new_longest,
                    today,
                    badge_3,
                    badge_7,
                    badge_14,
                    badge_30,
                    user_id,
                ),
            )
            return cur.fetchone()


def image_hash(image_bytes: bytes) -> str:
    return hashlib.md5(image_bytes).hexdigest()


def get_cached_image(img_hash: str) -> Optional[ImageCacheRow]:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT * FROM image_cache WHERE image_hash = %s", (img_hash,))
            return cur.fetchone()


def save_image_cache(
    img_hash: str,
    user_id: str,
    food_name: str,
    calories: float,
    protein: float,
    carbs: float,
    fat: float,
    portion_g: Optional[float] = None,
    confidence: float = 1.0,
    source: str = "groq",
) -> ImageCacheRow:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute(
                """
                INSERT INTO image_cache
                    (image_hash, user_id, food_name, calories, protein, carbs, fat, portion_g, confidence, source)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (image_hash) DO NOTHING
                RETURNING *
                """,
                (
                    img_hash,
                    user_id,
                    food_name,
                    calories,
                    protein,
                    carbs,
                    fat,
                    portion_g,
                    confidence,
                    source,
                ),
            )
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    "SELECT * FROM image_cache WHERE image_hash = %s", (img_hash,)
                )
                row = cur.fetchone()
            return row


def fetch_today_meals(user_id: str, for_date=None) -> list[dict]:
    """
    Return today's logs grouped by meal_id.
    Each meal has: dish_name, total macros, logged_at,
    image_b64, and list of ingredients.
    """
    from datetime import date as dt

    target = for_date or dt.today()

    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute(
                """
                SELECT
                    meal_id,
                    dish_name,
                    MIN(logged_at)   AS logged_at,
                    SUM(calories)    AS total_calories,
                    SUM(protein)     AS total_protein,
                    SUM(carbs)       AS total_carbs,
                    SUM(fat)         AS total_fat,
                    MAX(image_b64)   AS image_b64,
                    COUNT(*)         AS ingredient_count,
                    MAX(source)      AS source
                FROM food_logs
                WHERE user_id  = %s
                AND log_date = %s
                GROUP BY meal_id, dish_name
                ORDER BY MIN(logged_at) ASC
                """,
                (user_id, target),
            )
            meals = cur.fetchall()

            # Attach ingredients list to each meal
            result = []
            for meal in meals:
                cur.execute(
                    """
                    SELECT food_name, calories, protein, carbs,
                        fat, portion_g, confidence, source,
                        is_veg, flagged
                    FROM food_logs
                    WHERE user_id = %s
                    AND meal_id = %s
                    ORDER BY id ASC
                    """,
                    (user_id, meal["meal_id"]),
                )
                ingredients = cur.fetchall()
                meal_dict = dict(meal)
                meal_dict["ingredients"] = [dict(i) for i in ingredients]
                result.append(meal_dict)

            return result


def get_user_by_email(email: str) -> Optional[UserRow]:
    """Fetch user by email for login."""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            return cur.fetchone()


def create_user_with_password(
    user_id: str,
    name: str,
    email: str,
    password_hash: str,
) -> UserRow:
    """Create a new user with hashed password."""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute(
                """
                INSERT INTO users (id, name, email, password_hash)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
                RETURNING *
                """,
                (user_id, name, email, password_hash),
            )
            row = cur.fetchone()
            if row is None:
                cur.execute("SELECT * FROM users WHERE email = %s", (email,))
                row = cur.fetchone()

            # Auto create streak row
            cur.execute(
                """
                INSERT INTO streaks (user_id)
                VALUES (%s)
                ON CONFLICT (user_id) DO NOTHING
                """,
                (row["id"],),
            )
            return row


def update_password(user_id: str, password_hash: str) -> bool:
    """Update user password hash."""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (password_hash, user_id),
            )
            return cur.rowcount > 0
