-- ============================================================
-- Honey-Pot Scam Detection — Neon PostgreSQL Migration
-- Run this entire script in: Neon Console → SQL Editor
-- ============================================================

-- Sessions table: core conversation state
CREATE TABLE IF NOT EXISTS sessions (
    id                TEXT PRIMARY KEY,
    confidence        FLOAT   NOT NULL DEFAULT 1.0,
    turns             INT     NOT NULL DEFAULT 0,
    completed         BOOLEAN NOT NULL DEFAULT FALSE,
    scammer_type      TEXT             DEFAULT 'unknown',
    scammer_profile   TEXT,
    current_persona   TEXT,
    persona_history   JSONB            DEFAULT '[]',
    behavior_patterns JSONB            DEFAULT '{}',
    created_at        TIMESTAMPTZ      DEFAULT now(),
    last_activity     TIMESTAMPTZ      DEFAULT now()
);

-- Intelligence table: extracted scam indicators per session
CREATE TABLE IF NOT EXISTS intelligence (
    session_id          TEXT PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
    upi_ids             TEXT[]      DEFAULT '{}',
    phone_numbers       TEXT[]      DEFAULT '{}',
    phishing_links      TEXT[]      DEFAULT '{}',
    bank_accounts       TEXT[]      DEFAULT '{}',
    suspicious_keywords TEXT[]      DEFAULT '{}',
    scanned_text        TEXT[]      DEFAULT '{}',
    updated_at          TIMESTAMPTZ DEFAULT now()
);

-- Messages table: full conversation history
CREATE TABLE IF NOT EXISTS messages (
    id          BIGSERIAL PRIMARY KEY,
    session_id  TEXT        NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    sender      TEXT        NOT NULL,  -- 'scammer' | 'agent' | 'user'
    text        TEXT        NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_last_activity ON sessions(last_activity DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_completed ON sessions(completed);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);

-- ============================================================
-- Verification — run these SELECT statements to confirm setup
-- ============================================================
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
-- SELECT COUNT(*) FROM sessions;
