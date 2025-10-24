"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
import json
import uuid
from typing import Optional

# Simple in-memory session store for admin tokens -> username
sessions = {}

# Teachers store will be loaded from src/teachers.json
teachers = {}

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


def load_teachers():
    """Load teachers from `src/teachers.json`. For this exercise we store
    plaintext passwords in the JSON. Replace with hashed passwords in production."""
    global teachers
    try:
        base = Path(__file__).parent
        with open(base / "teachers.json", "r", encoding="utf-8") as f:
            teachers = json.load(f)
    except Exception:
        # if file is missing, default to empty
        teachers = {}


def get_token_from_request(request: Request) -> Optional[str]:
    # token can be provided as an http-only cookie or an X-Admin-Token header
    token = request.cookies.get("admin_token")
    if not token:
        token = request.headers.get("X-Admin-Token")
    return token


def require_teacher(request: Request):
    token = get_token_from_request(request)
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    return sessions[token]


@app.on_event("startup")
def startup_event():
    load_teachers()


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, request: Request):
    """Sign up a student for an activity. Restricted to logged-in teachers (admin)."""
    # require teacher permissions
    require_teacher(request)
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, request: Request):
    """Unregister a student from an activity. Restricted to logged-in teachers (admin)."""
    # require teacher permissions
    require_teacher(request)
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}


@app.post("/admin/login")
def admin_login(payload: dict, response: Response):
    """Login a teacher. Payload: {"username": "...", "password": "..."}

    NOTE: This implementation uses plaintext passwords from `src/teachers.json`.
    Replace with hashed passwords and secure verification for production.
    """
    username = payload.get("username")
    password = payload.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")

    if username not in teachers or teachers.get(username) != password:
        raise HTTPException(status_code=401, detail="invalid credentials")

    token = uuid.uuid4().hex
    sessions[token] = username
    # set cookie for browser-based clients
    response.set_cookie(key="admin_token", value=token, httponly=True, samesite='lax')
    return {"message": "logged in", "token": token}


@app.post("/admin/logout")
def admin_logout(request: Request, response: Response):
    token = get_token_from_request(request)
    if token and token in sessions:
        del sessions[token]
    response.delete_cookie("admin_token")
    return {"message": "logged out"}
