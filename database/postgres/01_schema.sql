-- ============================================================
-- AI Customer Service Platform — PostgreSQL Init Script
-- Runs automatically on first container start
-- ============================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── ENUMS ──────────────────────────────────────────────────
CREATE TYPE user_role AS ENUM ('customer', 'agent', 'supervisor', 'manager', 'admin');
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended');
CREATE TYPE case_status AS ENUM ('open', 'in_progress', 'pending_customer', 'escalated', 'resolved', 'closed');
CREATE TYPE case_priority AS ENUM ('low', 'medium', 'high', 'urgent');
CREATE TYPE case_category AS ENUM (
    'billing', 'technical_support', 'account', 'shipping',
    'returns', 'product_inquiry', 'complaint', 'feedback', 'other'
);
CREATE TYPE case_sentiment AS ENUM ('positive', 'neutral', 'negative');
CREATE TYPE case_source AS ENUM ('web', 'mobile', 'chatbot', 'email', 'phone');
CREATE TYPE audit_action AS ENUM (
    'login', 'logout', 'login_failed', 'token_refresh',
    'user_created', 'user_updated', 'user_deactivated',
    'case_created', 'case_updated', 'case_assigned', 'case_escalated', 'case_resolved',
    'ai_prediction', 'ai_override',
    'file_uploaded', 'file_deleted',
    'role_changed', 'permission_changed',
    'automation_triggered', 'notification_sent'
);
CREATE TYPE notification_type AS ENUM ('email', 'in_app', 'push');
CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'failed', 'read');
CREATE TYPE automation_trigger AS ENUM (
    'case_created', 'case_urgent', 'sentiment_negative',
    'case_inactivity', 'case_status_changed', 'case_resolved',
    'daily_summary', 'case_overdue'
);

-- ─── USERS ──────────────────────────────────────────────────
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    role            user_role NOT NULL DEFAULT 'customer',
    status          user_status NOT NULL DEFAULT 'active',
    phone           VARCHAR(50),
    avatar_url      TEXT,
    department      VARCHAR(100),
    team_id         UUID,
    mfa_enabled     BOOLEAN DEFAULT FALSE,
    mfa_secret      VARCHAR(255),
    last_login_at   TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ─── TEAMS ──────────────────────────────────────────────────
CREATE TABLE teams (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    manager_id  UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE users ADD CONSTRAINT fk_users_team
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL;

-- ─── REFRESH TOKENS ─────────────────────────────────────────
CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) UNIQUE NOT NULL,
    expires_at  TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked     BOOLEAN DEFAULT FALSE,
    ip_address  VARCHAR(45),
    user_agent  TEXT,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ─── CUSTOMERS ──────────────────────────────────────────────
CREATE TABLE customers (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    company        VARCHAR(255),
    account_tier   VARCHAR(50) DEFAULT 'standard',
    total_cases    INTEGER DEFAULT 0,
    created_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ─── CASES ──────────────────────────────────────────────────
CREATE TABLE cases (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_number         SERIAL UNIQUE,
    title               VARCHAR(500) NOT NULL,
    message             TEXT NOT NULL,
    category            case_category,
    priority            case_priority DEFAULT 'medium',
    sentiment           case_sentiment,
    status              case_status DEFAULT 'open',
    source              case_source DEFAULT 'web',
    customer_id         UUID NOT NULL REFERENCES users(id),
    assigned_to         UUID REFERENCES users(id) ON DELETE SET NULL,
    team_id             UUID REFERENCES teams(id) ON DELETE SET NULL,
    is_escalated        BOOLEAN DEFAULT FALSE,
    escalated_at        TIMESTAMP WITH TIME ZONE,
    escalation_reason   TEXT,
    sla_deadline        TIMESTAMP WITH TIME ZONE,
    resolved_at         TIMESTAMP WITH TIME ZONE,
    closed_at           TIMESTAMP WITH TIME ZONE,
    resolution_note     TEXT,
    ai_category         case_category,
    ai_priority         case_priority,
    ai_sentiment        case_sentiment,
    ai_confidence       FLOAT,
    ai_overridden       BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ─── CASE NOTES ─────────────────────────────────────────────
CREATE TABLE case_notes (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id     UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    author_id   UUID NOT NULL REFERENCES users(id),
    content     TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ─── CASE TIMELINE ──────────────────────────────────────────
CREATE TABLE case_timeline (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id      UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    actor_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type   VARCHAR(100) NOT NULL,
    description  TEXT NOT NULL,
    old_value    TEXT,
    new_value    TEXT,
    metadata     JSONB,
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ─── FILE ATTACHMENTS ───────────────────────────────────────
CREATE TABLE file_attachments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id         UUID REFERENCES cases(id) ON DELETE CASCADE,
    note_id         UUID REFERENCES case_notes(id) ON DELETE CASCADE,
    uploader_id     UUID NOT NULL REFERENCES users(id),
    filename        VARCHAR(255) NOT NULL,
    original_name   VARCHAR(255) NOT NULL,
    mime_type       VARCHAR(100) NOT NULL,
    size_bytes      BIGINT NOT NULL,
    storage_path    TEXT NOT NULL,
    is_deleted      BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ─── NOTIFICATIONS ───────────────────────────────────────────
CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recipient_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type            notification_type NOT NULL DEFAULT 'in_app',
    status          notification_status NOT NULL DEFAULT 'pending',
    subject         VARCHAR(500),
    body            TEXT NOT NULL,
    reference_type  VARCHAR(100),
    reference_id    UUID,
    read_at         TIMESTAMP WITH TIME ZONE,
    sent_at         TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ─── AUTOMATION LOGS ────────────────────────────────────────
CREATE TABLE automation_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trigger_type    automation_trigger NOT NULL,
    reference_id    UUID,
    status          VARCHAR(50) NOT NULL DEFAULT 'triggered',
    result          TEXT,
    error           TEXT,
    executed_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ─── AUDIT LOGS ─────────────────────────────────────────────
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id        UUID REFERENCES users(id) ON DELETE SET NULL,
    action          audit_action NOT NULL,
    resource_type   VARCHAR(100),
    resource_id     UUID,
    description     TEXT,
    ip_address      VARCHAR(45),
    user_agent      TEXT,
    metadata        JSONB,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ─── REPORTING / ANALYTICS ──────────────────────────────────
CREATE TABLE reporting_daily (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_date         DATE NOT NULL,
    total_cases         INTEGER DEFAULT 0,
    open_cases          INTEGER DEFAULT 0,
    resolved_cases      INTEGER DEFAULT 0,
    closed_cases        INTEGER DEFAULT 0,
    escalated_cases     INTEGER DEFAULT 0,
    avg_resolution_hrs  FLOAT,
    sentiment_positive  INTEGER DEFAULT 0,
    sentiment_neutral   INTEGER DEFAULT 0,
    sentiment_negative  INTEGER DEFAULT 0,
    chatbot_sessions    INTEGER DEFAULT 0,
    chatbot_resolved    INTEGER DEFAULT 0,
    chatbot_escalated   INTEGER DEFAULT 0,
    automations_fired   INTEGER DEFAULT 0,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(report_date)
);

CREATE TABLE reporting_agent_performance (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id            UUID NOT NULL REFERENCES users(id),
    report_date         DATE NOT NULL,
    cases_assigned      INTEGER DEFAULT 0,
    cases_resolved      INTEGER DEFAULT 0,
    avg_resolution_hrs  FLOAT,
    avg_satisfaction    FLOAT,
    escalations_handled INTEGER DEFAULT 0,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(agent_id, report_date)
);

-- ─── INDEXES ────────────────────────────────────────────────
CREATE INDEX idx_cases_customer_id     ON cases(customer_id);
CREATE INDEX idx_cases_assigned_to     ON cases(assigned_to);
CREATE INDEX idx_cases_status          ON cases(status);
CREATE INDEX idx_cases_priority        ON cases(priority);
CREATE INDEX idx_cases_created_at      ON cases(created_at DESC);
CREATE INDEX idx_case_notes_case_id    ON case_notes(case_id);
CREATE INDEX idx_case_timeline_case_id ON case_timeline(case_id);
CREATE INDEX idx_notifications_recip   ON notifications(recipient_id);
CREATE INDEX idx_audit_actor           ON audit_logs(actor_id);
CREATE INDEX idx_audit_created_at      ON audit_logs(created_at DESC);
CREATE INDEX idx_refresh_tokens_user   ON refresh_tokens(user_id);
CREATE INDEX idx_reporting_daily_date  ON reporting_daily(report_date DESC);

-- ─── TRIGGERS — auto update updated_at ──────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_cases_updated_at
    BEFORE UPDATE ON cases FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_case_notes_updated_at
    BEFORE UPDATE ON case_notes FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_teams_updated_at
    BEFORE UPDATE ON teams FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_customers_updated_at
    BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at();
