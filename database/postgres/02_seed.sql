-- ============================================================
-- Seed Data — Roles, Teams, Default Admin User
-- ============================================================

-- ─── Default Teams ──────────────────────────────────────────
INSERT INTO teams (id, name, description) VALUES
  ('11111111-1111-1111-1111-111111111111', 'Tier 1 Support',  'First-line customer support agents'),
  ('22222222-2222-2222-2222-222222222222', 'Tier 2 Support',  'Escalation and technical specialists'),
  ('33333333-3333-3333-3333-333333333333', 'Billing Team',    'Billing and account specialists'),
  ('44444444-4444-4444-4444-444444444444', 'Management',      'Supervisors and managers')
ON CONFLICT DO NOTHING;

-- ─── Default Admin User ─────────────────────────────────────
-- Password: Admin@123 (bcrypt hashed)
INSERT INTO users (id, email, hashed_password, full_name, role, status, department, team_id) VALUES
  (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'admin@csplatform.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKyOHMCdV3wSrKK',
    'System Administrator',
    'admin',
    'active',
    'IT Operations',
    '44444444-4444-4444-4444-444444444444'
  )
ON CONFLICT (email) DO NOTHING;

-- ─── Sample Manager ─────────────────────────────────────────
-- Password: Manager@123
INSERT INTO users (id, email, hashed_password, full_name, role, status, department, team_id) VALUES
  (
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'manager@csplatform.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKyOHMCdV3wSrKK',
    'Sarah Johnson',
    'manager',
    'active',
    'Customer Success',
    '44444444-4444-4444-4444-444444444444'
  )
ON CONFLICT (email) DO NOTHING;

-- ─── Sample Supervisor ──────────────────────────────────────
INSERT INTO users (id, email, hashed_password, full_name, role, status, department, team_id) VALUES
  (
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'supervisor@csplatform.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKyOHMCdV3wSrKK',
    'James Wilson',
    'supervisor',
    'active',
    'Customer Support',
    '11111111-1111-1111-1111-111111111111'
  )
ON CONFLICT (email) DO NOTHING;

-- ─── Sample Agents ──────────────────────────────────────────
INSERT INTO users (id, email, hashed_password, full_name, role, status, department, team_id) VALUES
  (
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    'agent1@csplatform.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKyOHMCdV3wSrKK',
    'Emily Carter',
    'agent',
    'active',
    'Customer Support',
    '11111111-1111-1111-1111-111111111111'
  ),
  (
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    'agent2@csplatform.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKyOHMCdV3wSrKK',
    'Marcus Thompson',
    'agent',
    'active',
    'Customer Support',
    '11111111-1111-1111-1111-111111111111'
  ),
  (
    'ffffffff-ffff-ffff-ffff-ffffffffffff',
    'agent3@csplatform.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKyOHMCdV3wSrKK',
    'Priya Patel',
    'agent',
    'active',
    'Billing',
    '33333333-3333-3333-3333-333333333333'
  ),
  (
    '77777777-dddd-dddd-dddd-dddddddddddd',
    'agent.mortgage@csplatform.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKyOHMCdV3wSrKK',
    'Mark Mortgage',
    'agent',
    'active',
    'Mortgages',
    '11111111-1111-1111-1111-111111111111'
  ),
  (
    '88888888-dddd-dddd-dddd-dddddddddddd',
    'agent.debt@csplatform.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKyOHMCdV3wSrKK',
    'Dana Debt',
    'agent',
    'active',
    'Collections',
    '11111111-1111-1111-1111-111111111111'
  ),
  (
    '99999999-dddd-dddd-dddd-dddddddddddd',
    'agent.credit@csplatform.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKyOHMCdV3wSrKK',
    'Craig Credit',
    'agent',
    'active',
    'Credit',
    '11111111-1111-1111-1111-111111111111'
  ),
  (
    'aaaaaaaa-dddd-dddd-dddd-dddddddddddd',
    'agent.banking@csplatform.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKyOHMCdV3wSrKK',
    'Beth Banking',
    'agent',
    'active',
    'General Banking',
    '11111111-1111-1111-1111-111111111111'
  ),
  (
    'bbbbbbbb-dddd-dddd-dddd-dddddddddddd',
    'agent.card@csplatform.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKyOHMCdV3wSrKK',
    'Cody Card',
    'agent',
    'active',
    'Credit Cards',
    '11111111-1111-1111-1111-111111111111'
  ),
  (
    'cccccccc-dddd-dddd-dddd-dddddddddddd',
    'agent.student@csplatform.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKyOHMCdV3wSrKK',
    'Steve Student',
    'agent',
    'active',
    'Student Loans',
    '11111111-1111-1111-1111-111111111111'
  )
ON CONFLICT (email) DO NOTHING;

-- ─── Sample Customer ────────────────────────────────────────
INSERT INTO users (id, email, hashed_password, full_name, role, status) VALUES
  (
    '00000000-0000-0000-0000-000000000001',
    'customer@csplatform.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKyOHMCdV3wSrKK',
    'Alex Reed',
    'customer',
    'active'
  )
ON CONFLICT (email) DO NOTHING;

INSERT INTO customers (user_id, account_tier) VALUES
  ('00000000-0000-0000-0000-000000000001', 'premium')
ON CONFLICT DO NOTHING;

-- ─── Update team managers ────────────────────────────────────
UPDATE teams SET manager_id = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'
WHERE id IN (
  '11111111-1111-1111-1111-111111111111',
  '44444444-4444-4444-4444-444444444444'
);
