CREATE EXTENSION IF NOT EXISTS postgis;
-- =============================================================================
-- GREENER - Database Initialization Script
-- =============================================================================
-- Target   : PostgreSQL 15+
-- Encoding : UTF-8
-- Version  : 2.0 (with gamification system)
-- Tables   : 18
-- Notes    : Execute this script on a fresh database.
--            Tables are created in dependency order (parents before children).
--            All primary keys are UUID with auto-generation via gen_random_uuid().
-- =============================================================================


-- ---------------------------------------------------------------------------
-- 0. EXTENSIONS
-- ---------------------------------------------------------------------------
-- gen_random_uuid() is native since PG 13, no extension needed.
-- PostGIS will be added later when the mobility module is implemented.
-- If you need it now, uncomment the line below:
-- CREATE EXTENSION IF NOT EXISTS postgis;


-- ===========================================================================
--  PART 1 — CORE TABLES
-- ===========================================================================


-- ---------------------------------------------------------------------------
-- 1. USERS
-- ---------------------------------------------------------------------------
-- Central table. Every other table references this one directly or indirectly.
-- password_hash stores a bcrypt/argon2 hash, never the plain-text password.
-- date_of_birth replaces the old "age" column: age is computed, not stored.
-- postal_code is VARCHAR(5) to preserve leading zeros (e.g. 06000 Nice).
CREATE TABLE users (
    id             UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    email          VARCHAR(255) NOT NULL,
    first_name     VARCHAR(100) NOT NULL,
    last_name      VARCHAR(100) NOT NULL,
    username       VARCHAR(50)  NOT NULL,
    date_of_birth  DATE,
    postal_code    VARCHAR(5),
    password_hash  VARCHAR(255) NOT NULL,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT uq_users_email    UNIQUE (email),
    CONSTRAINT uq_users_username UNIQUE (username)
);

CREATE INDEX idx_users_email ON users (email);


-- ---------------------------------------------------------------------------
-- 2. SESSIONS
-- ---------------------------------------------------------------------------
-- One user has one active session per device in this schema.
-- refresh_token_hash stores a SHA-256 of the refresh token, never the raw token.
-- revoked defaults to false; set to true on logout or expiry.
CREATE TABLE sessions (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash  VARCHAR(255) NOT NULL,
    device_info         VARCHAR(255),
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    expires_at          TIMESTAMPTZ  NOT NULL,
    revoked             BOOLEAN      NOT NULL DEFAULT false,

    CONSTRAINT uq_sessions_user_device UNIQUE (user_id, device_info)
);

CREATE INDEX idx_sessions_user_id ON sessions (user_id);
CREATE INDEX idx_sessions_expires ON sessions (expires_at)
    WHERE revoked = false;


-- ===========================================================================
--  PART 2 — GAMIFICATION
-- ===========================================================================


-- ---------------------------------------------------------------------------
-- 3. LEVELS
-- ---------------------------------------------------------------------------
-- Reference table: the 10 eco-citizen levels.
-- rank is the ordering key (1 = beginner, 10 = legend).
-- xp_required is the cumulative XP needed to reach this level.
-- Populated by seed data — the app never inserts into this table at runtime.
CREATE TABLE levels (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    rank         INTEGER      NOT NULL,
    name         VARCHAR(100) NOT NULL,
    xp_required  INTEGER      NOT NULL,

    CONSTRAINT uq_levels_rank UNIQUE (rank),
    CONSTRAINT ck_levels_rank_range CHECK (rank BETWEEN 1 AND 10),
    CONSTRAINT ck_levels_xp_positive CHECK (xp_required >= 0)
);


-- ---------------------------------------------------------------------------
-- 4. USER_GAME_PROFILES
-- ---------------------------------------------------------------------------
-- 1-to-1 with users. Separated to keep the users table focused on identity
-- and avoid loading gamification data on every auth check.
-- The user's current level is NOT stored: it is derived at query time by
-- comparing experience against the levels table. This avoids desynchronization.
--
-- Streak fields:
--   current_streak  — consecutive days right now (reset when broken)
--   longest_streak  — personal best (for profile stats)
--   total_login_days — cumulative total (for the "Fidele de Greener" badge at 100)
--   last_login_date — used to detect whether today continues the streak
CREATE TABLE user_game_profiles (
    id               UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    experience       INTEGER NOT NULL DEFAULT 0,
    current_streak   INTEGER NOT NULL DEFAULT 0,
    longest_streak   INTEGER NOT NULL DEFAULT 0,
    total_login_days INTEGER NOT NULL DEFAULT 0,
    last_login_date  DATE,

    CONSTRAINT uq_ugp_user_id UNIQUE (user_id),
    CONSTRAINT ck_ugp_experience_positive CHECK (experience >= 0),
    CONSTRAINT ck_ugp_streak_positive CHECK (current_streak >= 0),
    CONSTRAINT ck_ugp_longest_positive CHECK (longest_streak >= 0),
    CONSTRAINT ck_ugp_total_positive CHECK (total_login_days >= 0)
);


-- ---------------------------------------------------------------------------
-- 5. BADGES
-- ---------------------------------------------------------------------------
-- Catalog of all badges (~30 in v1). Seed data, not user-generated.
-- slug is the machine identifier used in back-end logic (e.g. 'first_scan').
-- category groups badges for display: streak, waste_dex, quiz, referral,
--   contribution, cross (transversal).
-- threshold is the numeric target to reach (5 wastes, 10 correct answers…).
--   NULL for badges with complex unlock logic handled in application code.
-- min_version tracks which app release makes the badge available (v1, v1.5, vmax).
CREATE TABLE badges (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    slug         VARCHAR(50)  NOT NULL,
    name         VARCHAR(100) NOT NULL,
    description  TEXT,
    category     VARCHAR(30)  NOT NULL,
    threshold    INTEGER,
    min_version  VARCHAR(10)  NOT NULL DEFAULT 'v1',

    CONSTRAINT uq_badges_slug UNIQUE (slug),
    CONSTRAINT ck_badges_category CHECK (
        category IN ('streak', 'waste_dex', 'quiz', 'referral', 'contribution', 'cross')
    )
);


-- ---------------------------------------------------------------------------
-- 6. USER_BADGES
-- ---------------------------------------------------------------------------
-- Junction: which user unlocked which badge, and when.
-- UNIQUE prevents earning the same badge twice.
CREATE TABLE user_badges (
    id        UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id   UUID        NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
    badge_id  UUID        NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
    earned_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_ub_user_badge UNIQUE (user_id, badge_id)
);

CREATE INDEX idx_ub_user_id  ON user_badges (user_id);
CREATE INDEX idx_ub_badge_id ON user_badges (badge_id);


-- ---------------------------------------------------------------------------
-- 7. DAILY_LOGINS
-- ---------------------------------------------------------------------------
-- One row per user per calendar day. Used to compute streaks and the
-- daily login quest (5 + (N-1)*2 pts, capped at 7-day cycles).
-- UNIQUE ensures at most one entry per day regardless of how many times
-- the user opens the app.
CREATE TABLE daily_logins (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    login_date  DATE NOT NULL DEFAULT CURRENT_DATE,

    CONSTRAINT uq_dl_user_date UNIQUE (user_id, login_date)
);

CREATE INDEX idx_dl_user_id ON daily_logins (user_id);


-- ---------------------------------------------------------------------------
-- 8. REFERRALS
-- ---------------------------------------------------------------------------
-- Tracks who invited whom. Points (50) are credited only when activated = true,
-- which requires the referee to complete their first action in the app.
-- referee_id is nullable: it is set when the invitee actually creates an account.
CREATE TABLE referrals (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    referrer_id   UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    referee_id    UUID        REFERENCES users(id) ON DELETE SET NULL,
    activated     BOOLEAN     NOT NULL DEFAULT false,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    activated_at  TIMESTAMPTZ
);

CREATE INDEX idx_referrals_referrer ON referrals (referrer_id);
CREATE INDEX idx_referrals_referee  ON referrals (referee_id)
    WHERE referee_id IS NOT NULL;


-- ---------------------------------------------------------------------------
-- 9. CONTRIBUTIONS
-- ---------------------------------------------------------------------------
-- User contributions to the collaborative map.
-- type determines the base points: 'comment' (3), 'reply' (2), 'missing_data' (15).
-- validated flips to true after moderation → triggers +10 bonus pts in app logic.
CREATE TABLE contributions (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type          VARCHAR(30) NOT NULL,
    validated     BOOLEAN     NOT NULL DEFAULT false,
    validated_at  TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_contributions_type CHECK (
        type IN ('comment', 'reply', 'missing_data')
    )
);

CREATE INDEX idx_contributions_user_id ON contributions (user_id);


-- ===========================================================================
--  PART 3 — WASTE / RECYCLING MODULE
-- ===========================================================================


-- ---------------------------------------------------------------------------
-- 10. WASTES
-- ---------------------------------------------------------------------------
-- Reference table: the catalog of known waste types.
-- Populated by seed data or by the AI classification pipeline.
-- bin indicates which bin the waste goes into (e.g. 'yellow', 'green', 'glass').
-- note is a free-text hint for the user (e.g. "rinse before discarding").
-- rarity determines WasteDex discovery points:
--   common (10), uncommon (25), rare (50), legendary (100).
CREATE TABLE wastes (
    id      UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    type    VARCHAR(100) NOT NULL,
    bin     VARCHAR(100) NOT NULL,
    note    TEXT,
    rarity  VARCHAR(20)  NOT NULL DEFAULT 'common',

    CONSTRAINT ck_wastes_rarity CHECK (
        rarity IN ('common', 'uncommon', 'rare', 'legendary')
    )
);


-- ---------------------------------------------------------------------------
-- 11. USER_WASTE_DEX
-- ---------------------------------------------------------------------------
-- Junction table: tracks which wastes a user has encountered (their "pokedex").
-- is_scanned = true if the user identified it via camera, false if manual entry.
-- UNIQUE prevents duplicate entries for the same user + waste pair.
CREATE TABLE user_waste_dex (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
    waste_id    UUID        NOT NULL REFERENCES wastes(id)  ON DELETE CASCADE,
    is_scanned  BOOLEAN     NOT NULL DEFAULT false,
    scanned_at  TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_uwd_user_waste UNIQUE (user_id, waste_id)
);

CREATE INDEX idx_uwd_user_id  ON user_waste_dex (user_id);
CREATE INDEX idx_uwd_waste_id ON user_waste_dex (waste_id);


-- ===========================================================================
--  PART 4 — SOCIAL / COMMUNITY MODULE
-- ===========================================================================


-- ---------------------------------------------------------------------------
-- 12. POSTS
-- ---------------------------------------------------------------------------
-- Social feed: a user shares an eco-action (text + optional photo).
-- updated_at is NULL until the post is edited; the app displays "edited" when set.
CREATE TABLE posts (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body        TEXT        NOT NULL,
    image_url   VARCHAR(500),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ
);

CREATE INDEX idx_posts_created ON posts (created_at DESC);
CREATE INDEX idx_posts_user_id ON posts (user_id);


-- ---------------------------------------------------------------------------
-- 13. COMMENTS
-- ---------------------------------------------------------------------------
-- A comment always belongs to exactly one post and one user.
CREATE TABLE comments (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
    post_id     UUID        NOT NULL REFERENCES posts(id)  ON DELETE CASCADE,
    body        TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_comments_post_id ON comments (post_id);
CREATE INDEX idx_comments_user_id ON comments (user_id);


-- ---------------------------------------------------------------------------
-- 14. REACTIONS
-- ---------------------------------------------------------------------------
-- A reaction targets either a post OR a comment, never both, never neither.
-- type is a short string: 'like', 'bravo', 'leaf', etc.
CREATE TABLE reactions (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES users(id)     ON DELETE CASCADE,
    post_id     UUID        REFERENCES posts(id)              ON DELETE CASCADE,
    comment_id  UUID        REFERENCES comments(id)           ON DELETE CASCADE,
    type        VARCHAR(30) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_reactions_one_target CHECK (
        (post_id IS NOT NULL AND comment_id IS NULL)
        OR
        (post_id IS NULL AND comment_id IS NOT NULL)
    ),
    CONSTRAINT uq_reactions_user_post    UNIQUE (user_id, post_id, type),
    CONSTRAINT uq_reactions_user_comment UNIQUE (user_id, comment_id, type)
);

CREATE INDEX idx_reactions_post_id    ON reactions (post_id)    WHERE post_id IS NOT NULL;
CREATE INDEX idx_reactions_comment_id ON reactions (comment_id) WHERE comment_id IS NOT NULL;


-- ===========================================================================
--  PART 5 — NUTRITION MODULE
-- ===========================================================================


-- ---------------------------------------------------------------------------
-- 15. NUTRITION
-- ---------------------------------------------------------------------------
-- Reference table: nutritional product catalog. Standalone for now.
-- JSONB columns store structured but flexible data from external APIs.
CREATE TABLE nutrition (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name                  VARCHAR(200) NOT NULL,
    production_countries  JSONB        NOT NULL DEFAULT '[]'::jsonb,
    nutritional_values    JSONB        NOT NULL DEFAULT '{}'::jsonb,
    preservation_method   JSONB        NOT NULL DEFAULT '[]'::jsonb,
    shelf_life            JSONB        NOT NULL DEFAULT '{}'::jsonb,
    health_benefits       JSONB        NOT NULL DEFAULT '[]'::jsonb,
    allergens             JSONB        NOT NULL DEFAULT '[]'::jsonb
);

CREATE INDEX idx_nutrition_name ON nutrition (name);


-- ===========================================================================
--  PART 6 — QUIZ MODULE
-- ===========================================================================


-- ---------------------------------------------------------------------------
-- 16. QUESTIONS
-- ---------------------------------------------------------------------------
-- Quiz questions for the sorting guide.
-- departments scopes questions to specific French departments (JSONB array).
-- Empty array = question available everywhere.
CREATE TABLE questions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question     TEXT  NOT NULL,
    departments  JSONB NOT NULL DEFAULT '[]'::jsonb
);


-- ---------------------------------------------------------------------------
-- 17. ANSWERS
-- ---------------------------------------------------------------------------
-- Each question has 1..N answer choices. Exactly one should have is_correct = true.
-- points determines how much XP a correct answer is worth (5 or 10).
CREATE TABLE answers (
    id           UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id  UUID    NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    body         TEXT    NOT NULL,
    is_correct   BOOLEAN NOT NULL DEFAULT false,
    points       INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT ck_answers_points_positive CHECK (points >= 0)
);

CREATE INDEX idx_answers_question_id ON answers (question_id);


-- ---------------------------------------------------------------------------
-- 18. USER_ANSWERS
-- ---------------------------------------------------------------------------
-- Tracks which answer a user picked. The 1-quiz-per-day cap is enforced
-- in application code by checking answered_at::date against CURRENT_DATE.
CREATE TABLE user_answers (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
    answer_id   UUID        NOT NULL REFERENCES answers(id) ON DELETE CASCADE,
    answered_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_ua_user_answer UNIQUE (user_id, answer_id)
);

CREATE INDEX idx_ua_user_id   ON user_answers (user_id);
CREATE INDEX idx_ua_answer_id ON user_answers (answer_id);


-- =============================================================================
-- END OF SCHEMA — 18 tables
-- =============================================================================
-- Next steps:
--   1. Run this file:  psql -U greener -d greener_db -f init.sql
--   2. Seed reference data:
--      - levels        (10 rows, the XP ladder)
--      - badges        (~30 rows, all badge definitions)
--      - wastes         (waste catalog with rarity tiers)
--      - questions      (20 quiz questions + their answers)
--      - nutrition      (product catalog from Open Food Facts)
--   3. Add PostGIS extension when the mobility module is ready
-- =============================================================================