-- ============================================================
-- NutriLens AI — PostgreSQL Setup
-- Run this entire script in PG Admin Query Tool
-- ============================================================


-- ------------------------------------------------------------
-- 1. USERS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id          TEXT        PRIMARY KEY,
    name        TEXT        NOT NULL,
    email       TEXT        UNIQUE,
    cal_goal    INTEGER     NOT NULL DEFAULT 2000,
    protein_g   INTEGER     NOT NULL DEFAULT 150,
    carbs_g     INTEGER     NOT NULL DEFAULT 200,
    fat_g       INTEGER     NOT NULL DEFAULT 65,
    diet_type   TEXT        NOT NULL DEFAULT 'maintain'
                            CHECK (diet_type IN ('cut', 'bulk', 'maintain')),
    units       TEXT        NOT NULL DEFAULT 'metric'
                            CHECK (units IN ('metric', 'imperial')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ------------------------------------------------------------
-- 2. FOOD LOGS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS food_logs (
    id          BIGSERIAL   PRIMARY KEY,
    user_id     TEXT        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    logged_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    food_name   TEXT        NOT NULL,
    portion_g   REAL,
    calories    REAL        NOT NULL DEFAULT 0,
    protein     REAL        NOT NULL DEFAULT 0,
    carbs       REAL        NOT NULL DEFAULT 0,
    fat         REAL        NOT NULL DEFAULT 0,
    image_b64   TEXT,
    confidence  REAL        NOT NULL DEFAULT 1.0
                            CHECK (confidence BETWEEN 0.0 AND 1.0),
    source      TEXT        NOT NULL DEFAULT 'groq'
                            CHECK (source IN ('groq', 'huggingface', 'manual')),
    notes       TEXT
);

CREATE INDEX IF NOT EXISTS idx_food_logs_user_date
    ON food_logs (user_id, (logged_at::DATE));

CREATE INDEX IF NOT EXISTS idx_food_logs_logged_at
    ON food_logs (user_id, logged_at DESC);


-- ------------------------------------------------------------
-- 3. STREAKS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS streaks (
    user_id     TEXT        PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    current     INTEGER     NOT NULL DEFAULT 0,
    longest     INTEGER     NOT NULL DEFAULT 0,
    last_log    DATE,
    badge_3     BOOLEAN     NOT NULL DEFAULT FALSE,
    badge_7     BOOLEAN     NOT NULL DEFAULT FALSE,
    badge_14    BOOLEAN     NOT NULL DEFAULT FALSE,
    badge_30    BOOLEAN     NOT NULL DEFAULT FALSE
);


-- ------------------------------------------------------------
-- 4. IMAGE CACHE
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS image_cache (
    image_hash  TEXT        PRIMARY KEY,
    user_id     TEXT        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    food_name   TEXT        NOT NULL,
    calories    REAL        NOT NULL,
    protein     REAL        NOT NULL,
    carbs       REAL        NOT NULL,
    fat         REAL        NOT NULL,
    portion_g   REAL,
    confidence  REAL        NOT NULL DEFAULT 1.0,
    source      TEXT        NOT NULL DEFAULT 'groq',
    cached_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ------------------------------------------------------------
-- 5. AUTO-UPDATE updated_at TRIGGER
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ------------------------------------------------------------
-- 6. DAILY TOTALS VIEW
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW daily_totals AS
SELECT
    user_id,
    logged_at::DATE         AS log_date,
    SUM(calories)           AS total_calories,
    SUM(protein)            AS total_protein,
    SUM(carbs)              AS total_carbs,
    SUM(fat)                AS total_fat,
    COUNT(*)                AS meal_count
FROM food_logs
GROUP BY user_id, logged_at::DATE;


-- ------------------------------------------------------------
-- 7. WEEKLY SUMMARY VIEW
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW weekly_summary AS
SELECT
    user_id,
    log_date,
    total_calories,
    total_protein,
    total_carbs,
    total_fat,
    meal_count
FROM daily_totals
WHERE log_date >= CURRENT_DATE - INTERVAL '6 days';


-- ------------------------------------------------------------
-- 8. SEED DATA
-- ------------------------------------------------------------
INSERT INTO users (id, name, email)
    VALUES ('guest', 'Guest', NULL)
    ON CONFLICT (id) DO NOTHING;

INSERT INTO streaks (user_id)
    VALUES ('guest')
    ON CONFLICT (user_id) DO NOTHING;