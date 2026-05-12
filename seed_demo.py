"""
Seed demo users into the auth service SQLite database.
Run: python seed_demo.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "services", "auth-service"))
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./auth.db"

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
import uuid
import hashlib


# Bcrypt hash using bcrypt directly (passlib has issues with Python 3.14)
def hash_pw(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


DEMO_USERS = [
    {"email": "admin@csplatform.local",    "password": "Admin@123",    "full_name": "Alex Admin",      "role": "admin",    "department": "IT"},
    {"email": "manager@csplatform.local",  "password": "Manager@123",  "full_name": "Maya Manager",    "role": "manager",  "department": "Operations"},
    {"email": "agent1@csplatform.local",   "password": "Agent@123",    "full_name": "Sam Agent",       "role": "agent",    "department": "Support"},
    {"email": "agent2@csplatform.local",   "password": "Agent@123",    "full_name": "Jordan Agent",    "role": "agent",    "department": "Support"},
    {"email": "customer@csplatform.local", "password": "Customer@123", "full_name": "Charlie Customer","role": "customer", "department": None},
]


async def seed():
    engine = create_async_engine("sqlite+aiosqlite:///./services/auth-service/auth.db", echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        # Create users table if not exists
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'customer',
                status TEXT NOT NULL DEFAULT 'active',
                phone TEXT,
                avatar_url TEXT,
                department TEXT,
                team_id TEXT,
                mfa_enabled INTEGER NOT NULL DEFAULT 0,
                mfa_secret TEXT,
                last_login_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT (datetime('now')),
                updated_at TIMESTAMP DEFAULT (datetime('now'))
            )
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                user_id TEXT NOT NULL,
                token_hash TEXT UNIQUE NOT NULL,
                revoked INTEGER NOT NULL DEFAULT 0,
                expires_at TIMESTAMP NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT (datetime('now'))
            )
        """))

    print("Seeding demo users...")
    async with session_factory() as db:
        for u in DEMO_USERS:
            user_id = str(uuid.uuid4())
            hashed = hash_pw(u["password"])
            try:
                await db.execute(text("""
                    INSERT OR IGNORE INTO users (id, email, hashed_password, full_name, role, status, department, mfa_enabled)
                    VALUES (:id, :email, :hashed_password, :full_name, :role, 'active', :department, 0)
                """), {
                    "id": user_id,
                    "email": u["email"],
                    "hashed_password": hashed,
                    "full_name": u["full_name"],
                    "role": u["role"],
                    "department": u.get("department"),
                })
                print(f"  OK: {u['email']} ({u['role']})")
            except Exception as e:
                print(f"  SKIP {u['email']}: {e}")
        await db.commit()

    print("\nDemo users ready!")
    print("Login at: http://localhost:3000/login")
    print("  admin@csplatform.local / Admin@123")
    print("  manager@csplatform.local / Manager@123")
    print("  agent1@csplatform.local / Agent@123")
    print("  customer@csplatform.local / Customer@123")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
