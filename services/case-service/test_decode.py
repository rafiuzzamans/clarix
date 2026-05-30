
from jose import jwt
from app.core.config import settings
try:
    print('Decoding...')
    payload = jwt.decode("None", settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    print('Payload:', payload)
except Exception as e:
    import traceback
    traceback.print_exc()
