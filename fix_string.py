"""
Fix String(36) used in non-SQLAlchemy contexts.
- In models/     : String(36) in Column(...) is CORRECT — leave alone
- In schemas/    : replace with str
- In routes/     : replace with str in function annotations
- In services/   : replace with str in function annotations
- String(36)(x)  : replace with str(x)
- String(36).uuid4() : replace with str(uuid.uuid4())
"""
import os
import re

BASE = r'C:\Project\services'

# Patterns to fix
FIXES_NON_MODEL = [
    # String(36)(some_value) -> str(some_value)
    (r'String\(36\)\(([^)]+)\)', r'str(\1)'),
    # String(36).uuid4() -> str(__import__('uuid').uuid4())
    (r"String\(36\)\.uuid4\(\)", "str(__import__('uuid').uuid4())"),
    # Type annotations: : String(36) -> : str
    (r':\s*String\(36\)', ': str'),
    # Optional[String(36)] -> Optional[str]
    (r'Optional\[String\(36\)\]', 'Optional[str]'),
    # -> String(36) return type
    (r'->\s*String\(36\)', '-> str'),
    # Bare String(36) not inside Column()
    # This catches remaining cases that aren't inside Column(...)
]

def is_model_file(path):
    # Only leave String(36) alone inside models/ directory
    return os.sep + 'models' + os.sep in path

def fix_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content

    if is_model_file(path):
        # In model files, only fix the broken patterns (not Column usages)
        fixes = FIXES_NON_MODEL[:2]  # Only fix String(36)(x) and String(36).uuid4()
    else:
        fixes = FIXES_NON_MODEL

    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content)

    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

total = 0
for root, dirs, files in os.walk(BASE):
    dirs[:] = [d for d in dirs if '__pycache__' not in d]
    for fname in files:
        if not fname.endswith('.py'):
            continue
        path = os.path.join(root, fname)
        if fix_file(path):
            total += 1
            print('Fixed:', os.path.relpath(path, BASE))

print(f'\nDone — fixed {total} files.')
