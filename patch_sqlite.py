"""
Properly fix all services for SQLite/local compatibility.
Replaces PostgreSQL-specific imports and types cleanly.
"""
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
SERVICES = [
    "auth-service", "user-service", "case-service",
    "analytics-service", "notification-service", "file-service"
]

FIXES = [
    # Fix broken "from String(36) import String(36)" lines from previous bad patch
    (r'^from String\(\d+\) import.*$', '', re.MULTILINE),
    (r'^import String\(\d+\).*$', '', re.MULTILINE),

    # Fix UUID imports from postgres dialect
    (r'from sqlalchemy\.dialects\.postgresql import\s+(?:UUID,?\s*)+,?\s*JSONB\s*\n',
     'from sqlalchemy import String, Text\n', 0),
    (r'from sqlalchemy\.dialects\.postgresql import\s+UUID,?\s*JSONB\s*\n',
     'from sqlalchemy import String, Text\n', 0),
    (r'from sqlalchemy\.dialects\.postgresql import\s+UUID\s*\n',
     'from sqlalchemy import String\n', 0),
    (r'from sqlalchemy\.dialects\.postgresql import\s+JSONB\s*\n',
     'from sqlalchemy import Text\n', 0),
    (r'from sqlalchemy\.dialects\.postgresql import[^\n]*\n',
     '# postgres dialect removed for sqlite compat\n', 0),

    # Fix UUID column type
    (r'UUID\(as_uuid=True\)', 'String(36)', 0),
    (r'\bUUID\b(?!\()', 'String(36)', 0),

    # Fix JSONB column type
    (r'\bJSONB\b', 'Text', 0),

    # Fix NOW() server_default (Postgres syntax → SQLite)
    (r"server_default=text\(['\"]NOW\(\)['\"]\)", "default=lambda: __import__('datetime').datetime.utcnow()", 0),
    (r"server_default=text\(['\"]CURRENT_TIMESTAMP['\"]\)", "default=lambda: __import__('datetime').datetime.utcnow()", 0),
    (r'server_default=func\.now\(\)', "default=lambda: __import__('datetime').datetime.utcnow()", 0),
    (r"server_default=\"NOW\(\)\"", "default=lambda: __import__('datetime').datetime.utcnow()", 0),
]


def fix_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    for pattern, replacement, flags in FIXES:
        content = re.sub(pattern, replacement, content, flags=flags)

    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


total = 0
for svc in SERVICES:
    svc_dir = os.path.join(BASE, "services", svc)
    if not os.path.isdir(svc_dir):
        continue
    for root, dirs, files in os.walk(svc_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fname in files:
            if fname.endswith(".py"):
                fpath = os.path.join(root, fname)
                if fix_file(fpath):
                    rel = os.path.relpath(fpath, BASE)
                    print(f"  Fixed: {rel}")
                    total += 1

print(f"\n✅ Fixed {total} files.")
