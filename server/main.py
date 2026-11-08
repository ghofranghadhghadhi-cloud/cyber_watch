import sqlite3
from fastapi import FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from database import get_connection, init_db
from security import hash_password, verify_password, create_token, decode_token

app = FastAPI(title="Cyber_Watch API")
init_db()


class RegisterData(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    email: str = Field(min_length=5, max_length=100)
    password: str = Field(min_length=8, max_length=64)


class LoginData(BaseModel):
    username: str
    password: str


@app.post("/api/register")
def register(data: RegisterData):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (data.username, data.email, hash_password(data.password)),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username or email already used")
    finally:
        conn.close()
    return {"message": "Account created"}


@app.post("/api/login")
def login(data: LoginData):
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (data.username,)
    ).fetchone()
    conn.close()

    if user is None or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Wrong username or password")

    token = create_token(user["username"], user["role"])
    return {"access_token": token, "username": user["username"], "role": user["role"]}


@app.get("/api/me")
def me(authorization: str = Header(default=None)):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    payload = decode_token(authorization.split(" ")[1])
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"username": payload["sub"], "role": payload["role"]}


@app.get("/api/health")
def health():
    return {"status": "online", "project": "Cyber_Watch"}


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def login_page():
    return FileResponse("static/login.html")


@app.get("/dashboard")
def dashboard_page():
    return FileResponse("static/dashboard.html")