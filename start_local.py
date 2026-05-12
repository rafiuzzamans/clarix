"""
Local development launcher — no Docker required.
Starts all FastAPI microservices using SQLite + local MongoDB.
Usage:  python start_local.py
"""
import subprocess
import sys
import os
import time
import signal
import threading

# ── Configuration ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON   = sys.executable

# Shared env vars injected into every service
SHARED_ENV = {
    **os.environ,
    # SQLite databases (one per service)
    "DATABASE_URL":              "sqlite+aiosqlite:///./csplatform_auth.db",
    "CASE_DATABASE_URL":         "sqlite+aiosqlite:///./csplatform_cases.db",
    "USER_DATABASE_URL":         "sqlite+aiosqlite:///./csplatform_users.db",
    "NOTIFICATION_DATABASE_URL": "sqlite+aiosqlite:///./csplatform_notifications.db",
    "ANALYTICS_DATABASE_URL":    "sqlite+aiosqlite:///./csplatform_analytics.db",
    "FILE_DATABASE_URL":         "sqlite+aiosqlite:///./csplatform_files.db",
    # MongoDB (already running locally)
    "MONGODB_URL":               "mongodb://localhost:27017",
    "MONGODB_DB":                "csplatform",
    # JWT secrets
    "SECRET_KEY":                "local-dev-secret-key-change-in-production",
    "REFRESH_SECRET_KEY":        "local-dev-refresh-secret-key",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
    "REFRESH_TOKEN_EXPIRE_DAYS":   "7",
    # Service URLs (localhost)
    "AUTH_SERVICE_URL":          "http://localhost:8001",
    "USER_SERVICE_URL":          "http://localhost:8002",
    "CASE_SERVICE_URL":          "http://localhost:8003",
    "AI_SERVICE_URL":            "http://localhost:8004",
    "CHATBOT_SERVICE_URL":       "http://localhost:8005",
    "AUTOMATION_SERVICE_URL":    "http://localhost:8006",
    "NOTIFICATION_SERVICE_URL":  "http://localhost:8007",
    "ANALYTICS_SERVICE_URL":     "http://localhost:8008",
    "FILE_SERVICE_URL":          "http://localhost:8009",
    "AUDIT_SERVICE_URL":         "http://localhost:8010",
    # SMTP (disabled locally)
    "SMTP_HOST": "localhost",
    "SMTP_PORT": "1025",
    # File uploads
    "UPLOAD_DIR": os.path.join(BASE_DIR, "uploads"),
    "MAX_FILE_SIZE": "20971520",
    # CORS
    "ALLOWED_ORIGINS": "http://localhost:3000,http://localhost:3001",
    # App
    "ENVIRONMENT": "development",
    "DEBUG": "true",
}

# Service definitions: (name, port, service_directory)
SERVICES = [
    ("Auth Service",         8001, "services/auth-service"),
    ("User Service",         8002, "services/user-service"),
    ("Case Service",         8003, "services/case-service"),
    ("AI Service",           8004, "services/ai-service"),
    ("Chatbot Service",      8005, "services/chatbot-service"),
    ("Automation Service",   8006, "services/automation-service"),
    ("Notification Service", 8007, "services/notification-service"),
    ("Analytics Service",    8008, "services/analytics-service"),
    ("File Service",         8009, "services/file-service"),
    ("Audit Service",        8010, "services/audit-service"),
]

processes = []

def log(msg, color=""):
    COLORS = {"green": "\033[92m", "red": "\033[91m", "yellow": "\033[93m",
               "cyan": "\033[96m", "bold": "\033[1m", "": ""}
    END = "\033[0m"
    print(f"{COLORS.get(color,'')}{msg}{END}", flush=True)


def start_service(name, port, rel_path):
    svc_dir = os.path.join(BASE_DIR, rel_path)
    if not os.path.isdir(svc_dir):
        log(f"  ⚠  {name}: directory not found — skipping", "yellow")
        return None

    env = {**SHARED_ENV}
    env["PORT"] = str(port)
    # Point DATABASE_URL to service-specific SQLite file
    db_name = rel_path.split("/")[-1].replace("-service", "")
    env["DATABASE_URL"] = f"sqlite+aiosqlite:///./{db_name}.db"

    cmd = [PYTHON, "-m", "uvicorn", "app.main:app",
           "--host", "0.0.0.0",
           "--port", str(port),
           "--reload",
           "--log-level", "warning"]

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=svc_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        processes.append((name, proc))
        log(f"  ✅  {name:<28} → http://localhost:{port}", "green")
        return proc
    except Exception as e:
        log(f"  ❌  {name}: {e}", "red")
        return None


def stream_logs(name, proc):
    """Background thread to print service logs."""
    prefix_colors = {
        "Auth":         "\033[94m",   # blue
        "User":         "\033[96m",   # cyan
        "Case":         "\033[92m",   # green
        "AI":           "\033[95m",   # magenta
        "Chatbot":      "\033[93m",   # yellow
        "Automation":   "\033[91m",   # red
        "Notification": "\033[97m",   # white
        "Analytics":    "\033[36m",   # dark cyan
        "File":         "\033[33m",   # orange
        "Audit":        "\033[35m",   # purple
    }
    tag = name.split()[0]
    color = prefix_colors.get(tag, "")
    END = "\033[0m"
    for line in proc.stdout:
        line = line.rstrip()
        if line and "INFO" not in line:
            print(f"{color}[{name[:12]:<12}]{END} {line}", flush=True)


def shutdown(sig=None, frame=None):
    log("\n🛑  Shutting down all services...", "yellow")
    for name, proc in processes:
        try:
            proc.terminate()
            log(f"  Stopped {name}", "yellow")
        except Exception:
            pass
    sys.exit(0)


def main():
    os.makedirs(SHARED_ENV["UPLOAD_DIR"], exist_ok=True)
    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    log("\n" + "═"*60, "bold")
    log("  🤖  AI Customer Service Platform — Local Runner", "bold")
    log("═"*60, "bold")
    log(f"  Python:  {sys.version.split()[0]}", "cyan")
    log(f"  MongoDB: mongodb://localhost:27017", "cyan")
    log(f"  DB:      SQLite (per-service files)", "cyan")
    log("═"*60 + "\n", "bold")

    log("Starting microservices...", "bold")
    for name, port, path in SERVICES:
        proc = start_service(name, port, path)
        if proc:
            t = threading.Thread(target=stream_logs, args=(name, proc), daemon=True)
            t.start()
        time.sleep(0.5)   # stagger startup

    log("\n" + "─"*60)
    log("🌐  Web App:  cd web-app && npm run dev  →  http://localhost:3000", "cyan")
    log("📧  Swagger docs: http://localhost:8001/docs  (Auth)", "cyan")
    log("🤖  AI docs:      http://localhost:8004/docs", "cyan")
    log("─"*60)
    log("\n⏳  Services starting... (allow ~10 seconds)", "yellow")
    log("   Press Ctrl+C to stop all services\n", "yellow")

    # Keep running, print status every 30s
    try:
        while True:
            time.sleep(30)
            alive = [(n, p) for n, p in processes if p.poll() is None]
            dead  = [(n, p) for n, p in processes if p.poll() is not None]
            if dead:
                for name, _ in dead:
                    log(f"  ⚠  {name} stopped unexpectedly", "red")
            log(f"  💚  {len(alive)}/{len(processes)} services running", "green")
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
