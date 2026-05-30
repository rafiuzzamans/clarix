import os

services = [
    'notification-service', 'file-service', 'chatbot-service',
    'automation-service', 'audit-service', 'analytics-service'
]
base_path = r'c:\Project\services'
for svc in services:
    path = os.path.join(base_path, svc, 'app', 'main.py')
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('allow_origins=["*"]', 'allow_origins=["http://localhost:3000", "http://localhost"]')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
print('CORS configs fixed.')
