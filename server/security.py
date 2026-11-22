import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

# The secret key comes from the environment, never from the code.
SECRET_KEY = os.environ.get("SECRET_KEY")
if SECRET_KEY is None:
    # Local development only. On the server, SECRET_KEY is always set.
    if os.environ.get("APP_ENV") == "production":
        raise RuntimeError("SECRET_KEY must be set in production")
    SECRET_KEY = "local-dev-key"

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