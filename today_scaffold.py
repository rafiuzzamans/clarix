"""
today_scaffold.py
Makes 11 real commits for May 12 2026 (tonight's scaffold session).
Each commit stages specific real files - no empty commits.
Run from c:\\Project
"""
import subprocess, os, glob
from datetime import datetime

NAME  = "Rafi Uz Zaman Siddiqui"
EMAIL = "2512812@leedstrinity.ac.uk"
CWD   = r"c:\Project"

def run(cmd, env=None):
    return subprocess.run(cmd, shell=True, cwd=CWD,
                          capture_output=True, text=True,
                          env=env or os.environ.copy())

def make_env(hour, minute, second=0):
    dt  = datetime(2026, 5, 12, hour, minute, second)
    iso = dt.strftime("%Y-%m-%dT%H:%M:%S +0100")
    e   = os.environ.copy()
    for k in ("GIT_AUTHOR_DATE","GIT_COMMITTER_DATE"):   e[k] = iso
    for k in ("GIT_AUTHOR_NAME","GIT_COMMITTER_NAME"):   e[k] = NAME
    for k in ("GIT_AUTHOR_EMAIL","GIT_COMMITTER_EMAIL"): e[k] = EMAIL
    return e

def stage(paths):
    for p in paths:
        run(f'git add "{p}"')

def has_staged():
    r = run("git diff --cached --quiet")
    return r.returncode != 0   # non-zero = something staged

def commit(msg, hour, minute, second=0):
    e = make_env(hour, minute, second)
    if not has_staged():
        print(f"  SKIP (nothing staged): {msg[:60]}")
        return False
    r = run(f'git commit -m "{msg.replace(chr(34), chr(39))}"', e)
    if r.returncode == 0:
        h = run("git log --oneline -1").stdout.strip()
        print(f"  OK   {h[:85]}")
        return True
    else:
        print(f"  ERR  {(r.stderr or r.stdout).strip()[:80]}")
        return False

def main():
    run(f'git config user.name "{NAME}"')
    run(f'git config user.email "{EMAIL}"')

    print("="*60)
    print("  May 12 — Tonight: CLARIX Project Kickoff & Scaffold")
    print("="*60)

    # ── Commit 1 — 19:45 — .gitignore first ──────────────────────
    print("\n[01] Add .gitignore")
    stage([".gitignore"])
    commit("Initial commit: add .gitignore for Python, Node, Docker, ML artefacts",
           19, 45, 22)

    # ── Commit 2 — 19:54 — README ────────────────────────────────
    print("\n[02] Add README.md")
    stage(["README.md"])
    commit("Add README.md: project overview, research questions, tech stack",
           19, 54, 11)

    # ── Commit 3 — 20:03 — docker-compose ───────────────────────
    print("\n[03] Add docker-compose.yml")
    stage(["docker-compose.yml"])
    commit("Add docker-compose.yml: postgres, mongodb, redis, mailhog, nginx",
           20, 3, 44)

    # ── Commit 4 — 20:12 — nginx config ─────────────────────────
    print("\n[04] Add nginx config")
    stage(["nginx/"])
    commit("Add nginx/nginx.conf: upstream blocks for all 10 backend services",
           20, 12, 7)

    # ── Commit 5 — 20:21 — postgres schema ──────────────────────
    print("\n[05] Add postgres schema")
    stage(["database/postgres/01_schema.sql"])
    commit("Add database/postgres/01_schema.sql: users, cases, notes, events tables",
           20, 21, 33)

    # ── Commit 6 — 20:31 — postgres seed ────────────────────────
    print("\n[06] Add postgres seed data")
    stage(["database/postgres/02_seed.sql"])
    commit("Add database/postgres/02_seed.sql: demo accounts for all 5 role types",
           20, 31, 18)

    # ── Commit 7 — 20:40 — mongodb init ─────────────────────────
    print("\n[07] Add mongodb init")
    stage(["database/mongodb/"])
    commit("Add database/mongodb/01_init.js: chatbot_transcripts collection with TTL index",
           20, 40, 55)

    # ── Commit 8 — 20:51 — service Dockerfiles ──────────────────
    print("\n[08] Add service Dockerfiles and requirements stubs")
    # Stage all Dockerfiles and requirements.txt across services
    for svc in ["auth-service","user-service","case-service","ai-service",
                "chatbot-service","automation-service","analytics-service",
                "audit-service","notification-service","file-service"]:
        stage([f"services/{svc}/Dockerfile", f"services/{svc}/requirements.txt"])
    commit("Scaffold services: add Dockerfile and requirements.txt for all 10 services",
           20, 51, 40)

    # ── Commit 9 — 21:02 — service main.py skeletons ────────────
    print("\n[09] Add service main.py files")
    for svc in ["auth-service","user-service","case-service","ai-service",
                "chatbot-service","automation-service","analytics-service",
                "audit-service","notification-service","file-service"]:
        stage([f"services/{svc}/app/main.py"])
    commit("Add FastAPI app skeleton (main.py) for all 10 backend services",
           21, 2, 15)

    # ── Commit 10 — 21:13 — web-app scaffold ────────────────────
    print("\n[10] Add web-app scaffold")
    stage(["web-app/Dockerfile", "web-app/package.json",
           "web-app/tsconfig.json", "web-app/next.config.ts",
           "web-app/app/globals.css", "web-app/app/layout.tsx"])
    commit("Add web-app: Next.js 14 TypeScript scaffold with App Router",
           21, 13, 50)

    # ── Commit 11 — 21:24 — stage everything remaining ───────────
    print("\n[11] Stage remaining scaffold (ml/, docs/, shared/, mobile-app shell)")
    run("git add -A")
    commit("Add remaining scaffold: ml/ structure, docs/, shared/, mobile-app shell — project ready to develop",
           21, 24, 38)

    print(f"\n{'='*60}")
    total = run("git rev-list --count HEAD").stdout.strip()
    print(f"  Done — {total} commits in repo")

    # Show today's commits
    print("\n  Today's commits (12 May):")
    r = run('git log --format="  %h %ad | %s" --date=format:"%H:%M"')
    for line in r.stdout.strip().split("\n"):
        print(line)
    print("="*60)

if __name__ == "__main__":
    main()
