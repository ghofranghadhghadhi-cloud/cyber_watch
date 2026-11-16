import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

SECRET_KEY = "change-this-secret-key-before-deploy"
ALGORITHM = "HS256"
TOKEN_HOURS = 8


def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_token(username, role):
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_HOURS)
    data = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None


# Create a long random token for the agent (starts with cw_)
def create_agent_token():
    return "cw_" + secrets.token_urlsafe(32)


# Hash the agent token before saving it (we never store the real token)
def hash_agent_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()