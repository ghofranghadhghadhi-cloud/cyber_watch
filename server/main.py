import sqlite3
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from database import get_connection, init_db
from security import (
    hash_password,
    verify_password,
    create_token,
    decode_token,
    create_agent_token,
    hash_agent_token,
)

app = FastAPI(title="Cyber_Watch API")
init_db()


# ---------- Data models ----------
class RegisterData(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    email: str = Field(min_length=5, max_length=100)
    password: str = Field(min_length=8, max_length=64)


class LoginData(BaseModel):
    username: str
    password: str


class DeviceData(BaseModel):
    ip: str = Field(max_length=45)
    mac: str = Field(max_length=17)
    vendor: str = Field(default="Unknown", max_length=100)
    hostname: str = Field(default="-", max_length=100)


class ScanData(BaseModel):
    public_ip: Optional[str] = Field(default=None, max_length=45)
    devices: List[DeviceData]


# ---------- Helpers: who is calling the API? ----------
# Website user: checks the JWT token in the Authorization header
def get_user_from_jwt(authorization):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    payload = decode_token(authorization.split(" ")[1])
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (payload["sub"],)
    ).fetchone()
    conn.close()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# Agent: checks the agent token in the X-Agent-Token header
def get_user_id_from_agent_token(agent_token):
    if agent_token is None:
        raise HTTPException(status_code=401, detail="Missing agent token")
    conn = get_connection()
    row = conn.execute(
        "SELECT user_id FROM agent_tokens WHERE token_hash = ?",
        (hash_agent_token(agent_token),),
    ).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid agent token")
    return row["user_id"]


# ---------- Authentication routes ----------
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
    user = get_user_from_jwt(authorization)
    return {"username": user["username"], "role": user["role"]}


# ---------- Agent token ----------
# The user asks for a new agent token (the old one stops working)
@app.post("/api/agent/token")
def make_agent_token(authorization: str = Header(default=None)):
    user = get_user_from_jwt(authorization)
    token = create_agent_token()
    conn = get_connection()
    conn.execute("DELETE FROM agent_tokens WHERE user_id = ?", (user["id"],))
    conn.execute(
        "INSERT INTO agent_tokens (user_id, token_hash) VALUES (?, ?)",
        (user["id"], hash_agent_token(token)),
    )
    conn.commit()
    conn.close()
    return {"agent_token": token, "note": "Save it now. It is shown only once."}


# ---------- Scans sent by the agent ----------
@app.post("/api/scans")
def receive_scan(data: ScanData, x_agent_token: str = Header(default=None)):
    user_id = get_user_id_from_agent_token(x_agent_token)

    if len(data.devices) > 512:
        raise HTTPException(status_code=400, detail="Too many devices in one scan")

    conn = get_connection()
    conn.execute(
        "INSERT INTO scans (user_id, public_ip, device_count) VALUES (?, ?, ?)",
        (user_id, data.public_ip, len(data.devices)),
    )
    for device in data.devices:
        conn.execute(
            """
            INSERT INTO devices (user_id, ip, mac, vendor, hostname)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (user_id, mac) DO UPDATE SET
                ip = excluded.ip,
                vendor = excluded.vendor,
                hostname = excluded.hostname,
                last_seen = CURRENT_TIMESTAMP
            """,
            (user_id, device.ip, device.mac, device.vendor, device.hostname),
        )
    conn.commit()
    conn.close()
    return {"message": "Scan saved", "devices": len(data.devices)}


# ---------- Data for the dashboard ----------
# Each user sees only his own devices
@app.get("/api/devices")
def list_devices(authorization: str = Header(default=None)):
    user = get_user_from_jwt(authorization)
    conn = get_connection()
    rows = conn.execute(
        "SELECT ip, mac, vendor, hostname, first_seen, last_seen "
        "FROM devices WHERE user_id = ? ORDER BY last_seen DESC",
        (user["id"],),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
# History of the last scans of the user (for the dashboard chart)
@app.get("/api/scans")
def list_scans(authorization: str = Header(default=None)):
    user = get_user_from_jwt(authorization)
    conn = get_connection()
    rows = conn.execute(
        "SELECT public_ip, device_count, created_at "
        "FROM scans WHERE user_id = ? ORDER BY id DESC LIMIT 20",
        (user["id"],),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows] 

@app.get("/api/health")
def health():
    return {"status": "online", "project": "Cyber_Watch"}


# ---------- Pages ----------
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def login_page():
    return FileResponse("static/login.html")


@app.get("/dashboard")
def dashboard_page():
    return FileResponse("static/dashboard.html")
