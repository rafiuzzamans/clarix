import requests
import json
import os

token = requests.post('http://localhost/api/auth/login', json={'email': 'manager@csplatform.local', 'password': 'Manager@123'}).json().get('access_token')

code = f"""
from jose import jwt
from app.core.config import settings
try:
    print('Decoding...')
    payload = jwt.decode("{token}", settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    print('Payload:', payload)
except Exception as e:
    import traceback
    traceback.print_exc()
"""
with open('test_decode.py', 'w') as f:
    f.write(code)

os.system('docker cp test_decode.py cs_case:/app/test_decode.py')
os.system('docker exec cs_case python /app/test_decode.py')
