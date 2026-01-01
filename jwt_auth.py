import jwt
from fastapi import WebSocket
from datetime import datetime, timezone

SECRET = "SECRET123"
ALGO = "HS256"

def create_jwt(payload: dict, expires_in_sec=3600):
    exp = datetime.now(timezone.utc).timestamp() + expires_in_sec
    payload.update({"exp": exp})
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def verify_jwt(token: str):
    try:
        decoded = jwt.decode(token, SECRET, algorithms=[ALGO])
        return decoded
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
