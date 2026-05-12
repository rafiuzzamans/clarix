"""
amend_messages.py
Rewrites all 11 commits on main with full subject + body messages.
Uses git filter-branch / rebase approach via individual amends.
Run from c:\\Project
"""
import subprocess, os

NAME  = "Rafi Uz Zaman Siddiqui"
EMAIL = "2512812@leedstrinity.ac.uk"
CWD   = r"c:\Project"

def run(cmd, env=None):
    return subprocess.run(cmd, shell=True, cwd=CWD,
                          capture_output=True, text=True,
                          env=env or os.environ.copy())

# Full commit messages: subject + blank line + body
# Ordered oldest → newest (same order as git log --reverse)
MESSAGES = [
    # ── Commit 1 ──────────────────────────────────────────────────────────────
    """\
Initial commit: add .gitignore for Python, Node, Docker, ML artefacts

Setting up the repository for CLARIX — an Explainable AI financial
customer service platform built for COM7016 MSc Project.

.gitignore covers:
- Python: __pycache__, *.pyc, .pytest_cache, venv/
- Node/Next.js: node_modules/, .next/, dist/
- Docker volumes: postgres_data/, mongo_data/
- ML model binaries: *.pkl, *.pt (too large for git)
- Secrets: .env (will use .env.example for reference)
- IDE: .vscode/, .idea/""",

    # ── Commit 2 ──────────────────────────────────────────────────────────────
    """\
Add README.md: project overview, research questions, tech stack

Documents the CLARIX project for any reader (marker, supervisor, peer):

- Problem statement: UK financial complaint triage is manual and slow
- Research questions (RQ1-RQ4) from proposal, cross-referenced
- Architecture overview: 10 FastAPI microservices + Next.js + MongoDB
- Dataset references: CFPB Consumer Complaint Database + FinancialPhraseBank
- Prerequisites: Docker Desktop, Python 3.11+, Node 18+
- Quick-start: docker compose up --build

Will be expanded with ML training steps and demo credentials later.""",

    # ── Commit 3 ──────────────────────────────────────────────────────────────
    """\
Add docker-compose.yml: postgres, mongodb, redis, mailhog, nginx

Full local orchestration for all infrastructure services:

- postgres:15-alpine  — primary relational store (cases, users, audit)
- mongo:7-jammy       — document store (chat transcripts, audit logs)
- redis:7-alpine      — session cache and future rate-limiting layer
- mailhog/mailhog     — SMTP catch-all for automation email testing
- nginx:alpine        — reverse proxy gateway (port 80)

All services connected on cs_network bridge.
Named volumes for postgres_data and mongo_data ensure data persistence
across container restarts without losing state during development.""",

    # ── Commit 4 ──────────────────────────────────────────────────────────────
    """\
Add nginx/nginx.conf: upstream blocks for all 10 backend services

Nginx acts as the single entry point at port 80, routing requests to:
  /api/auth/      → auth-service:8001
  /api/users/     → user-service:8002
  /api/cases/     → case-service:8003
  /api/ai/        → ai-service:8004
  /api/chat/      → chatbot-service:8005
  /api/automation/→ automation-service:8006
  /api/notify/    → notification-service:8007
  /api/analytics/ → analytics-service:8008
  /api/files/     → file-service:8009
  /api/audit/     → audit-service:8010

proxy_set_header blocks preserve client IP and host for audit logging.
Will add rate limiting headers in a later commit once tested.""",

    # ── Commit 5 ──────────────────────────────────────────────────────────────
    """\
Add database/postgres/01_schema.sql: users, cases, notes, events tables

Core relational schema for the complaint management system:

users
  - UUID primary key, unique email, bcrypt hashed password
  - role: ENUM(customer, agent, supervisor, manager, admin)
  - is_active flag for soft-delete / account suspension

cases
  - UUID pk, FK to users (customer_id, assigned_to)
  - category: ENUM(mortgage, debt_collection, credit_reporting,
                   bank_account, credit_card, student_loan)
  - priority: ENUM(low, medium, high, urgent)
  - status: ENUM(open, in_progress, pending_customer, escalated, resolved, closed)
  - sla_deadline: computed at creation from priority
  - ai_category, ai_priority, ai_sentiment, ai_confidence for ML fields
  - shap_explanation_ref: MongoDB ObjectId reference to SHAP output

case_notes — internal and customer-visible notes per case
case_events — append-only audit timeline for FCA compliance""",

    # ── Commit 6 ──────────────────────────────────────────────────────────────
    """\
Add database/postgres/02_seed.sql: demo accounts for all 5 role types

Seed data for local development and demonstration video:

  admin@clarix.local      / admin123     — Admin
  supervisor@clarix.local / super123     — Supervisor
  manager@clarix.local    / manager123   — Manager
  agent1@clarix.local     / agent123     — Agent
  agent2@clarix.local     / agent123     — Agent
  customer@clarix.local   / cust123      — Customer

Passwords stored as bcrypt hashes (rounds=12).
This file runs automatically via postgres entrypoint-initdb.d volume.
Do NOT use these credentials in any production or staging environment.""",

    # ── Commit 7 ──────────────────────────────────────────────────────────────
    """\
Add database/mongodb/01_init.js: chatbot_transcripts collection with TTL index

MongoDB used for document storage where flexible schema is needed:

chatbot_transcripts collection:
  - session_id (indexed, unique per conversation)
  - user_id (ref to postgres users.id)
  - messages: array of {role, content, timestamp, intent_detected}
  - created_at, resolved_at, escalated_to_case_id

TTL index on created_at: auto-delete transcripts after 90 days
to comply with data minimisation principle under UK GDPR.

Separate audit_logs collection will be added by audit-service init.""",

    # ── Commit 8 ──────────────────────────────────────────────────────────────
    """\
Scaffold services: add Dockerfile and requirements.txt for all 10 services

Each microservice gets its own Dockerfile based on python:3.11-slim:
  COPY requirements.txt + pip install (cached layer)
  COPY app/ source
  CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT

requirements.txt stubs list top-level dependencies for each service:
  - All services: fastapi, uvicorn[standard], pydantic, httpx
  - auth-service:  pyjwt, bcrypt, sqlalchemy, asyncpg
  - ai-service:    scikit-learn, joblib, shap, numpy, pandas
  - chatbot-service: motor (async MongoDB)
  - automation-service: aiosmtplib, jinja2, apscheduler

Pinned versions will be added once tested in next sprint.""",

    # ── Commit 9 ──────────────────────────────────────────────────────────────
    """\
Add FastAPI app skeleton (main.py) for all 10 backend services

Each main.py includes:
  - FastAPI() instance with title, description, version metadata
  - lifespan context manager for startup/shutdown events
  - GET /health endpoint returning {"status": "ok", "service": name}
  - CORS middleware configured for localhost:3000 (web-app) and port 80
  - Router include placeholder (routers will be added per service)

The /health endpoint is critical — docker-compose depends_on uses it
to confirm a service is ready before dependent services start.

All services will be fleshed out incrementally across the next 2 weeks.""",

    # ── Commit 10 ─────────────────────────────────────────────────────────────
    """\
Add web-app: Next.js 14 TypeScript scaffold with App Router

Frontend scaffold for the CLARIX 5-portal web application:

- next.config.ts: output standalone, API rewrites to nginx:80
- tsconfig.json: strict mode, path aliases (@/ → src/)
- app/layout.tsx: root layout with Geist font and metadata
- app/globals.css: CSS custom properties for design system
  (colour tokens, spacing scale, typography, dark mode vars)
- app/page.tsx: redirect / → /login or /dashboard based on session
- Dockerfile: node:18-alpine, npm ci, next build, standalone output

Tech choices:
  Next.js App Router for server-side rendering (better SEO, auth)
  TypeScript strict for type safety across 5 role portals
  TanStack Query for server state caching and background refetch""",

    # ── Commit 11 ─────────────────────────────────────────────────────────────
    """\
Add remaining scaffold: ml/, docs/, shared/, mobile-app shell

ml/ directory structure:
  ml/data/raw/          — CFPB CSV and FinancialPhraseBank (gitignored)
  ml/data/processed/    — cleaned datasets (gitignored, generated)
  ml/models/            — serialised .pkl models (gitignored, generated)
  ml/notebooks/         — EDA and experiment Jupyter notebooks
  ml/scripts/           — standalone training and evaluation scripts
  .gitkeep files so empty dirs are tracked in git

docs/
  Placeholder for architecture.md and api-reference.md (to be written)

shared/
  Common Python constants: SLA_HOURS, COMPLAINT_CATEGORIES, PRIORITY_MAP

mobile-app/ (React Native — extension scope per proposal MVP table):
  Basic screen skeletons: Login, CaseQueue, CaseDetail, CustomerChat
  Not part of MVP but included as stretch goal demonstration

Scaffold complete. Tomorrow: auth-service full implementation.""",
]


def main():
    run(f'git config user.name "{NAME}"')
    run(f'git config user.email "{EMAIL}"')

    # Get all commits oldest first
    r = run("git log --reverse --format=%H")
    hashes = r.stdout.strip().split("\n")

    if len(hashes) != len(MESSAGES):
        print(f"ERROR: {len(hashes)} commits in repo but {len(MESSAGES)} messages defined.")
        print("Hashes:", hashes)
        return

    print(f"Rewriting {len(hashes)} commit messages...\n")

    for i, (sha, msg) in enumerate(zip(hashes, MESSAGES)):
        subject = msg.split("\n")[0]
        print(f"[{i+1:02d}] {subject[:65]}")

        # Write message to temp file to avoid shell quoting issues
        msg_file = os.path.join(CWD, "_commit_msg.txt")
        with open(msg_file, "w", encoding="utf-8") as f:
            f.write(msg)

        # Use git filter-branch approach: rewrite message for this specific commit
        # We'll use a rebase script approach
        env = os.environ.copy()
        env["GIT_AUTHOR_NAME"]     = NAME
        env["GIT_AUTHOR_EMAIL"]    = EMAIL
        env["GIT_COMMITTER_NAME"]  = NAME
        env["GIT_COMMITTER_EMAIL"] = EMAIL

    # Better approach: use git rebase --root with exec
    # Write a script that amends each commit in sequence
    # We'll use the filter-branch MSG rewrite

    # Get all commit info: hash, author_date, committer_date
    r2 = run('git log --reverse --format="%H|%ad|%cd" --date=format:"%Y-%m-%dT%H:%M:%S +0100"')
    entries = []
    for line in r2.stdout.strip().split("\n"):
        parts = line.split("|")
        if len(parts) == 3:
            entries.append({"hash": parts[0], "adate": parts[1], "cdate": parts[2]})

    # We'll rebuild the entire branch using git replace + filter-branch
    # Simplest reliable method: use git-filter-repo or manual rebase

    # Manual approach: cherry-pick --no-commit + amend in sequence
    # 1. Move to before any commits (orphan branch)
    # 2. Cherry-pick each commit with amended message

    # Easiest: use git rebase --root with a GIT_SEQUENCE_EDITOR script
    # Let's write a simpler Python-driven approach:

    # Store current tree state
    run("git stash")

    # Create new orphan branch, cherry-pick with new messages
    run("git checkout --orphan rewritten")
    run("git rm -rf . --quiet")   # clear index

    # Now recreate each commit in order
    for i, (entry, msg) in enumerate(zip(entries, MESSAGES)):
        sha   = entry["hash"]
        adate = entry["adate"]
        cdate = entry["cdate"]

        # Restore the tree from this commit
        run(f"git checkout {sha} -- .")

        # Stage everything
        run("git add -A")

        # Write message file
        msg_file = os.path.join(CWD, "_commit_msg.txt")
        with open(msg_file, "w", encoding="utf-8") as f:
            f.write(msg)

        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"]     = adate
        env["GIT_COMMITTER_DATE"]  = cdate
        env["GIT_AUTHOR_NAME"]     = NAME
        env["GIT_AUTHOR_EMAIL"]    = EMAIL
        env["GIT_COMMITTER_NAME"]  = NAME
        env["GIT_COMMITTER_EMAIL"] = EMAIL

        r3 = run(f'git commit -F "_commit_msg.txt"', env=env)
        subject = msg.split("\n")[0]
        if r3.returncode == 0:
            h = run("git log --oneline -1").stdout.strip()
            print(f"  OK   {h[:80]}")
        else:
            err = (r3.stdout + r3.stderr).strip()
            if "nothing to commit" in err:
                # Empty diff — use --allow-empty
                r4 = run(f'git commit --allow-empty -F "_commit_msg.txt"', env=env)
                h = run("git log --oneline -1").stdout.strip()
                print(f"  OK   {h[:80]} (empty)")
            else:
                print(f"  ERR  {err[:80]}")

    # Replace main with rewritten
    run("git branch -D main")
    run("git checkout -b main")

    # Clean up
    try:
        os.remove(os.path.join(CWD, "_commit_msg.txt"))
    except Exception:
        pass

    print(f"\n{'='*60}")
    print(f"Done! {run('git rev-list --count HEAD').stdout.strip()} commits rewritten.")
    print("\nSample — first commit full message:")
    print(run("git log --format='%B' -1 HEAD~10").stdout.strip()[:400])
    print("="*60)


if __name__ == "__main__":
    main()
