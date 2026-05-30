import os, glob, re

services_dir = r'c:\Project\services'
config_files = glob.glob(os.path.join(services_dir, '*-service/app/core/config.py'))

target_sqlite = re.compile(r'return f\s*[\'\"].*?sqlite\+aiosqlite:.*?[\'\"]')
replacement_pg = 'return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"'

for f in config_files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if target_sqlite.search(content):
        new_content = target_sqlite.sub(replacement_pg, content)
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f'Updated {f}')
