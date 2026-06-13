"""
Auth router — signup, login, logout, and current user endpoints.
"""

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.auth import SignUpRequest, LoginRequest, AuthResponse
from app.models.profile import ProfileResponse
from app.services import auth_service
from app.services import profile_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=AuthResponse, status_code=201)
async def signup(data: SignUpRequest):
    """
    Register a new user.

    - Creates a Supabase Auth user
    - Creates a profile in the `profiles` table
    - Creates role-specific profile (`student_profiles` or `worker_profiles`)
    - Returns access & refresh tokens
    """
    return await auth_service.signup_user(data)


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest):
    """
    Login with email + password.

    Returns access & refresh tokens along with user info.
    """
    return await auth_service.login_user(data)


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    """
    Logout the current user.

    Note: Supabase JWTs are stateless — this endpoint is a no-op on the
    server side. The client should discard the token locally.
    """
    return {"message": "Logged out successfully. Please discard your token."}


@router.get("/me", response_model=ProfileResponse)
async def get_me(user: dict = Depends(get_current_user)):
    """
    Get the currently authenticated user's full profile.
    """
    return await profile_service.get_profile_by_id(user["id"])
