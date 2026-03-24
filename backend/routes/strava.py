import os
import httpx
from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from db import get_conn

router = APIRouter()

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REDIRECT_URI = os.getenv("STRAVA_REDIRECT_URI", "http://localhost:8000/api/strava/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


@router.get("/auth")
def strava_auth(user_id: str):
    """Redirect user to Strava OAuth. Pass ?user_id=<id>"""
    url = (
        f"https://www.strava.com/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&approval_prompt=auto"
        f"&scope=activity:read_all"
        f"&state={user_id}"
    )
    return RedirectResponse(url)


@router.get("/callback")
def strava_callback(code: str, state: str):
    """Strava redirects here after auth. state = user_id"""
    resp = httpx.post("https://www.strava.com/oauth/token", data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
    })
    data = resp.json()

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO strava_tokens (user_id, access_token, refresh_token, expires_at)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE
        SET access_token=EXCLUDED.access_token,
            refresh_token=EXCLUDED.refresh_token,
            expires_at=EXCLUDED.expires_at
    """, (state, data["access_token"], data["refresh_token"], data["expires_at"]))
    conn.commit()
    cur.close()
    conn.close()

    return RedirectResponse(f"{FRONTEND_URL}?strava=connected")


@router.get("/status")
def strava_status(user_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM strava_tokens WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return {"connected": row is not None}
