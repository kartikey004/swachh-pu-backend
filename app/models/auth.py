"""
Pydantic schemas for authentication endpoints.
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ── Request Schemas ──────────────────────────────────────────

class SignUpRequest(BaseModel):
    """Body for POST /auth/signup."""

    email: EmailStr
    password: str = Field(..., min_length=6, description="Minimum 6 characters")
    name: str = Field(..., min_length=1)
    role: str = Field(..., pattern="^(student|worker|admin)$")
    phone: Optional[str] = None

    # Student-specific (required when role == student)
    roll_no: Optional[str] = None
    address: Optional[str] = None
    hostel: Optional[str] = None

    # Worker-specific (optional when role == worker)
    employee_id: Optional[str] = None
    zone: Optional[str] = None


class LoginRequest(BaseModel):
    """Body for POST /auth/login."""

    email: EmailStr
    password: str


# ── Response Schemas ─────────────────────────────────────────

class AuthUser(BaseModel):
    """Minimal user info returned after auth."""

    id: str
    email: str
    name: str
    role: str


class AuthResponse(BaseModel):
    """Returned on successful login / signup."""

    access_token: str
    refresh_token: str
    user: AuthUser
    message: str = "success"
