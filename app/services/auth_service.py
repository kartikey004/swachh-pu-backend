"""
Auth service — wraps Supabase Auth calls for signup and login.
"""

from fastapi import HTTPException, status

from app.models.auth import SignUpRequest, LoginRequest, AuthResponse, AuthUser
from app.utils.supabase_client import get_supabase_client, get_supabase_admin


async def signup_user(data: SignUpRequest) -> AuthResponse:
    """
    1. Create user in Supabase Auth
    2. Insert into `profiles` table
    3. Insert into `student_profiles` or `worker_profiles` based on role
    4. Return tokens + user info
    """
    supabase = get_supabase_client()
    admin = get_supabase_admin()

    # ── Step 1: Supabase Auth sign-up ──
    try:
        auth_response = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password,
        })
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Signup failed: {str(exc)}",
        )

    auth_user = auth_response.user
    session = auth_response.session

    if auth_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signup failed — user was not created. Check if the email is already registered.",
        )

    # ── Step 2: Insert into profiles ──
    profile_data = {
        "user_id": str(auth_user.id),
        "name": data.name,
        "role": data.role,
        "phone": data.phone,
    }

    try:
        profile_result = (
            admin.table("profiles")
            .insert(profile_data)
            .execute()
        )
        profile = profile_result.data[0]
    except Exception as exc:
        # Rollback: delete the auth user if profile insert fails
        try:
            admin.auth.admin.delete_user(str(auth_user.id))
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create profile: {str(exc)}",
        )

    # ── Step 3: Insert role-specific profile ──
    try:
        if data.role == "student":
            if not data.roll_no:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="roll_no is required for student signup",
                )
            admin.table("student_profiles").insert({
                "profile_id": profile["id"],
                "roll_no": data.roll_no,
                "address": data.address,
                "hostel": data.hostel,
            }).execute()

        elif data.role == "worker":
            admin.table("worker_profiles").insert({
                "profile_id": profile["id"],
                "employee_id": data.employee_id,
                "zone": data.zone,
            }).execute()

        # admin role has no extra profile table

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create role-specific profile: {str(exc)}",
        )

    # ── Step 4: Build response ──
    access_token = session.access_token if session else ""
    refresh_token = session.refresh_token if session else ""

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=AuthUser(
            id=str(auth_user.id),
            email=data.email,
            name=data.name,
            role=data.role,
        ),
        message="Signup successful",
    )


async def login_user(data: LoginRequest) -> AuthResponse:
    """Authenticate with email + password, return tokens."""
    supabase = get_supabase_client()
    admin = get_supabase_admin()

    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password,
        })
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {str(exc)}",
        )

    auth_user = auth_response.user
    session = auth_response.session

    if auth_user is None or session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Fetch profile
    profile_result = (
        admin.table("profiles")
        .select("*")
        .eq("user_id", str(auth_user.id))
        .execute()
    )

    if not profile_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    profile = profile_result.data[0]

    return AuthResponse(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        user=AuthUser(
            id=str(auth_user.id),
            email=data.email,
            name=profile["name"],
            role=profile["role"],
        ),
        message="Login successful",
    )
