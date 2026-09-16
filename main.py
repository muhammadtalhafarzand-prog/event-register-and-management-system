import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv


# =========================================================
# ENV
# =========================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY must be added to .env"
    )

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="EventFlow API",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# REQUEST MODELS
# =========================================================

class AuthData(BaseModel):
    email: str
    password: str


class EventCreate(BaseModel):
    title: str
    discribtion: Optional[str] = None
    data: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[str] = "active"


class EventUpdate(BaseModel):
    title: Optional[str] = None
    discribtion: Optional[str] = None
    data: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[str] = None


class ProfileCreate(BaseModel):
    id: str
    full_name: str
    role: Optional[str] = None


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None


class RegistrationCreate(BaseModel):
    user_id: str
    event_id: str
    status: Optional[str] = "registered"


class RegistrationUpdate(BaseModel):
    status: str


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():
    return {
        "success": True,
        "message": "EventFlow FastAPI backend is working"
    }


# =========================================================
# AUTH - REGISTER
# =========================================================

@app.post("/register")
def register(data: AuthData):

    try:
        result = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password
        })

        if not result.user:
            raise HTTPException(
                status_code=400,
                detail="Registration failed"
            )

        return {
            "success": True,
            "message": "Account created successfully",
            "user": {
                "id": result.user.id,
                "email": result.user.email
            },
            "session": result.session
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# =========================================================
# AUTH - LOGIN
# =========================================================

@app.post("/login")
def login(data: AuthData):

    try:
        result = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })

        if not result.user or not result.session:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        return {
            "success": True,
            "message": "Login successful",
            "user": {
                "id": result.user.id,
                "email": result.user.email
            },
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )


# =========================================================
# AUTH - LOGOUT
# =========================================================

@app.post("/logout")
def logout():

    try:
        supabase.auth.sign_out()

        return {
            "success": True,
            "message": "Logged out successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# AUTH - CURRENT USER
# =========================================================

def get_current_user(authorization: Optional[str]):

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format"
        )

    token = authorization.replace("Bearer ", "")

    try:
        user_response = supabase.auth.get_user(token)

        if not user_response.user:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )

        return user_response.user

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )


@app.get("/me")
def get_me(
    authorization: Optional[str] = Header(None)
):

    user = get_current_user(authorization)

    return {
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email
        }
    }


# =========================================================
# EVENTS - CREATE
# =========================================================

@app.post("/events")
def create_event(event: EventCreate):

    try:
        result = (
            supabase
            .table("event")
            .insert(event.model_dump(exclude_none=True))
            .execute()
        )

        return {
            "success": True,
            "message": "Event created successfully",
            "data": result.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# EVENTS - GET ALL
# =========================================================

@app.get("/events")
def get_events():

    try:
        result = (
            supabase
            .table("event")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        return {
            "success": True,
            "data": result.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# EVENTS - GET ONE
# =========================================================

@app.get("/events/{event_id}")
def get_event(event_id: str):

    try:
        result = (
            supabase
            .table("event")
            .select("*")
            .eq("id", event_id)
            .single()
            .execute()
        )

        return {
            "success": True,
            "data": result.data
        }

    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )


# =========================================================
# EVENTS - UPDATE
# =========================================================

@app.put("/events/{event_id}")
def update_event(
    event_id: str,
    event: EventUpdate
):

    try:
        data = event.model_dump(exclude_none=True)

        result = (
            supabase
            .table("event")
            .update(data)
            .eq("id", event_id)
            .execute()
        )

        return {
            "success": True,
            "message": "Event updated successfully",
            "data": result.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# EVENTS - DELETE
# =========================================================

@app.delete("/events/{event_id}")
def delete_event(event_id: str):

    try:
        result = (
            supabase
            .table("event")
            .delete()
            .eq("id", event_id)
            .execute()
        )

        return {
            "success": True,
            "message": "Event deleted successfully",
            "data": result.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# PROFILE - CREATE
# =========================================================

@app.post("/profiles")
def create_profile(profile: ProfileCreate):

    try:
        result = (
            supabase
            .table("profile")
            .insert(profile.model_dump(exclude_none=True))
            .execute()
        )

        return {
            "success": True,
            "message": "Profile created successfully",
            "data": result.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# PROFILE - GET
# =========================================================

@app.get("/profiles/{user_id}")
def get_profile(user_id: str):

    try:
        result = (
            supabase
            .table("profile")
            .select("*")
            .eq("id", user_id)
            .single()
            .execute()
        )

        return {
            "success": True,
            "data": result.data
        }

    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )


# =========================================================
# PROFILE - UPDATE
# =========================================================

@app.put("/profiles/{user_id}")
def update_profile(
    user_id: str,
    profile: ProfileUpdate
):

    try:
        data = profile.model_dump(exclude_none=True)

        result = (
            supabase
            .table("profile")
            .update(data)
            .eq("id", user_id)
            .execute()
        )

        return {
            "success": True,
            "message": "Profile updated successfully",
            "data": result.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# REGISTRATION - CREATE
# =========================================================

@app.post("/registrations")
def create_registration(
    registration: RegistrationCreate
):

    try:

        existing = (
            supabase
            .table("registration")
            .select("*")
            .eq("user_id", registration.user_id)
            .eq("event_id", registration.event_id)
            .execute()
        )

        if existing.data:
            raise HTTPException(
                status_code=400,
                detail="Already registered for this event"
            )

        result = (
            supabase
            .table("registration")
            .insert(
                registration.model_dump(exclude_none=True)
            )
            .execute()
        )

        return {
            "success": True,
            "message": "Registration successful",
            "data": result.data
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# REGISTRATION - USER REGISTRATIONS
# =========================================================

@app.get("/registrations/user/{user_id}")
def get_user_registrations(user_id: str):

    try:
        result = (
            supabase
            .table("registration")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        return {
            "success": True,
            "data": result.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# REGISTRATION - EVENT REGISTRATIONS
# =========================================================

@app.get("/registrations/event/{event_id}")
def get_event_registrations(event_id: str):

    try:
        result = (
            supabase
            .table("registration")
            .select("*")
            .eq("event_id", event_id)
            .execute()
        )

        return {
            "success": True,
            "data": result.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# REGISTRATION - UPDATE STATUS
# =========================================================

@app.put("/registrations/{registration_id}")
def update_registration(
    registration_id: str,
    registration: RegistrationUpdate
):

    try:
        result = (
            supabase
            .table("registration")
            .update({
                "status": registration.status
            })
            .eq("id", registration_id)
            .execute()
        )

        return {
            "success": True,
            "message": "Registration status updated",
            "data": result.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# REGISTRATION - DELETE
# =========================================================

@app.delete("/registrations/{registration_id}")
def delete_registration(registration_id: str):

    try:
        result = (
            supabase
            .table("registration")
            .delete()
            .eq("id", registration_id)
            .execute()
        )

        return {
            "success": True,
            "message": "Registration deleted successfully",
            "data": result.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )