import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


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

    # Worker-specific (required when role == worker)
    employee_id: Optional[str] = None
    zone: Optional[str] = None

    @field_validator("password", mode="before")
    @classmethod
    def validate_password_not_empty(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("Password must be a string.")
        if not v or not v.strip():
            raise ValueError("Password cannot be empty or contain only whitespace.")
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        return v

    @field_validator("email", mode="before")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("Email must be a string.")
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError("Email cannot be empty.")
        if not EMAIL_REGEX.match(v_stripped):
            raise ValueError("Invalid email format. Must match standard email format (e.g. user@example.com).")
        return v_stripped

    @field_validator("name", mode="before")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("Name must be a string.")
        if not v or not v.strip():
            raise ValueError("Name cannot be empty or contain only whitespace.")
        return v.strip()

    @field_validator("role", mode="before")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("Role must be a string.")
        if not v or not v.strip():
            raise ValueError("Role cannot be empty.")
        v_clean = v.strip().lower()
        if v_clean not in ["student", "worker", "admin"]:
            raise ValueError("Role must be one of: student, worker, admin.")
        return v_clean

    @field_validator("phone")
    @classmethod
    def validate_phone_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_stripped = v.strip()
            if not v_stripped:
                return None
            # Standard E.164 or 10-digit number pattern
            if not re.match(r"^\+?[1-9]\d{1,14}$|^[0-9]{10}$", v_stripped):
                raise ValueError("Phone number must be a valid format (e.g. a 10-digit number).")
            return v_stripped
        return v

    @model_validator(mode="after")
    def validate_role_specific_fields(self) -> "SignUpRequest":
        if self.role == "student":
            if not self.roll_no or not self.roll_no.strip():
                raise ValueError("roll_no is required for student role")
        elif self.role == "worker":
            if not self.employee_id or not self.employee_id.strip():
                raise ValueError("employee_id is required for worker role")
            if not self.zone or not self.zone.strip():
                raise ValueError("zone is required for worker role")
        return self


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
