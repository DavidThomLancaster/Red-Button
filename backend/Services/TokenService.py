

from jose import jwt, JWTError
from datetime import datetime, timedelta

SECRET_KEY = "supersecret"  # move to env var later
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 900000

class TokenService:
    @staticmethod
    def create_token(user_id: str):
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {"user_id": user_id, "exp": expire}
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def validate_token(token: str):
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None