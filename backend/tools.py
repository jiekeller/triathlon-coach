import os
import time
import httpx
from db import get_conn

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")


# ---------- Strava ----------

def _get_valid_strava_token(user_id: str) -> str | None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM strava_tokens WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    # Refresh if expired
    if row["expires_at"] < int(time.time()):
        resp = httpx.post("https://www.strava.com/oauth/token", data={
            "client_id": STRAVA_CLIENT_ID,
            "client_secret": STRAVA_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": row["refresh_token"],
        })
        data = resp.json()
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            UPDATE strava_tokens SET access_token=%s, refresh_token=%s, expires_at=%s
            WHERE user_id=%s
        """, (data["access_token"], data["refresh_token"], data["expires_at"], user_id))
        conn.commit()
        cur.close()
        conn.close()
        return data["access_token"]

    return row["access_token"]


def get_recent_activities(user_id: str, count: int = 10) -> dict:
    token = _get_valid_strava_token(user_id)
    if not token:
        return {"error": "No Strava account connected. Ask the user to connect Strava at /api/strava/auth."}

    resp = httpx.get(
        "https://www.strava.com/api/v3/athlete/activities",
        headers={"Authorization": f"Bearer {token}"},
        params={"per_page": count},
    )
    activities = resp.json()

    # Return a trimmed summary so we don't blow up the context
    summary = []
    for a in activities:
        summary.append({
            "date": a.get("start_date_local", "")[:10],
            "type": a.get("sport_type", a.get("type", "")),
            "name": a.get("name", ""),
            "distance_km": round(a.get("distance", 0) / 1000, 2),
            "duration_min": round(a.get("moving_time", 0) / 60, 1),
            "elevation_m": a.get("total_elevation_gain", 0),
            "avg_hr": a.get("average_heartrate"),
            "perceived_exertion": a.get("perceived_exertion"),
        })
    return {"activities": summary}


# ---------- Training plan ----------

def get_training_plan(user_id: str) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT plan, race_date, race_type FROM training_plans WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return {"plan": None, "message": "No training plan found. Ask the user for their race date and type to create one."}
    return {"plan": row["plan"], "race_date": str(row["race_date"]), "race_type": row["race_type"]}


def save_training_plan(user_id: str, plan: str, race_date: str, race_type: str) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO training_plans (user_id, plan, race_date, race_type)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE
        SET plan=EXCLUDED.plan, race_date=EXCLUDED.race_date,
            race_type=EXCLUDED.race_type, updated_at=NOW()
    """, (user_id, plan, race_date, race_type))
    conn.commit()
    cur.close()
    conn.close()
    return {"saved": True}


# ---------- Nutrition ----------

NUTRITION_PROFILES = {
    "sprint": {"daily_carbs_g": 300, "daily_protein_g": 130, "daily_fat_g": 80},
    "olympic": {"daily_carbs_g": 380, "daily_protein_g": 140, "daily_fat_g": 85},
    "70.3": {"daily_carbs_g": 450, "daily_protein_g": 150, "daily_fat_g": 90},
    "ironman": {"daily_carbs_g": 550, "daily_protein_g": 160, "daily_fat_g": 95},
}

LOAD_MULTIPLIERS = {"light": 0.8, "moderate": 1.0, "heavy": 1.3}


def get_nutrition_and_grocery_list(race_type: str, training_load: str) -> dict:
    profile = NUTRITION_PROFILES.get(race_type.lower(), NUTRITION_PROFILES["olympic"])
    multiplier = LOAD_MULTIPLIERS.get(training_load.lower(), 1.0)

    carbs = round(profile["daily_carbs_g"] * multiplier)
    protein = round(profile["daily_protein_g"] * multiplier)
    fat = round(profile["daily_fat_g"] * multiplier)
    calories = carbs * 4 + protein * 4 + fat * 9

    return {
        "daily_targets": {
            "calories": calories,
            "carbs_g": carbs,
            "protein_g": protein,
            "fat_g": fat,
        },
        "weekly_grocery_list": {
            "proteins": ["Chicken breast (2 kg)", "Eggs (2 dozen)", "Greek yogurt (1 kg)", "Canned tuna (6 cans)", "Cottage cheese (500g)"],
            "carbs": ["Oats (1 kg)", "Sweet potatoes (2 kg)", "Brown rice (1 kg)", "Whole grain bread (2 loaves)", "Bananas (2 bunches)", "Pasta (500g)"],
            "fats": ["Avocados (4)", "Olive oil (1 bottle)", "Mixed nuts (500g)", "Nut butter (1 jar)"],
            "recovery_and_hydration": ["Electrolyte tablets or powder", "Tart cherry juice (1 L)", "Chocolate milk (2 L)", "Medjool dates (500g)"],
            "vegetables": ["Spinach / mixed greens (500g)", "Broccoli (2 heads)", "Bell peppers (6)", "Berries — mixed frozen (1 kg)"],
        },
        "timing_tips": [
            "2–3 hrs before training: oats + banana + nut butter",
            "During sessions >90 min: 30–60g carbs/hr (dates, gels, sports drink)",
            "Within 30 min after: 3:1 carb-to-protein ratio (chocolate milk works great)",
            "Evening: prioritise protein + veggies for recovery",
        ]
    }


# ---------- Tool definitions for Claude ----------

TOOL_DEFINITIONS = [
    {
        "name": "get_recent_activities",
        "description": "Fetch the user's recent workouts from Strava. Returns date, type, distance, duration, HR, and elevation for each session.",
        "input_schema": {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "Number of recent activities to fetch (default 10, max 30)"}
            },
            "required": []
        }
    },
    {
        "name": "get_training_plan",
        "description": "Retrieve the user's current triathlon training plan and race details from the database.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "save_training_plan",
        "description": "Save or update the user's training plan in the database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "plan": {"type": "string", "description": "The full training plan as markdown text"},
                "race_date": {"type": "string", "description": "Race date in YYYY-MM-DD format"},
                "race_type": {"type": "string", "description": "sprint, olympic, 70.3, or ironman"}
            },
            "required": ["plan", "race_date", "race_type"]
        }
    },
    {
        "name": "get_nutrition_and_grocery_list",
        "description": "Generate nutrition targets and a weekly grocery shopping list based on race type and current training load.",
        "input_schema": {
            "type": "object",
            "properties": {
                "race_type": {"type": "string", "description": "sprint, olympic, 70.3, or ironman"},
                "training_load": {"type": "string", "description": "light, moderate, or heavy — based on this week's training volume"}
            },
            "required": ["race_type", "training_load"]
        }
    }
]


def execute_tool(name: str, inputs: dict, user_id: str) -> str:
    import json
    if name == "get_recent_activities":
        result = get_recent_activities(user_id, inputs.get("count", 10))
    elif name == "get_training_plan":
        result = get_training_plan(user_id)
    elif name == "save_training_plan":
        result = save_training_plan(user_id, inputs["plan"], inputs["race_date"], inputs["race_type"])
    elif name == "get_nutrition_and_grocery_list":
        result = get_nutrition_and_grocery_list(inputs["race_type"], inputs["training_load"])
    else:
        result = {"error": f"Unknown tool: {name}"}
    return json.dumps(result)
