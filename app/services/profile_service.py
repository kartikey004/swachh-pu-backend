"""
Profile service — Supabase queries for profile CRUD.
"""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status

from app.models.profile import (
    ProfileResponse,
    StudentProfileDetail,
    WorkerProfileDetail,
    UpdateProfileRequest,
)
from app.utils.supabase_client import get_supabase_admin


def _build_profile_response(profile: dict, student: Optional[dict], worker: Optional[dict]) -> ProfileResponse:
    """Helper to assemble a ProfileResponse from raw DB rows."""
    student_detail = None
    worker_detail = None

    if student:
        student_detail = StudentProfileDetail(
            roll_no=student["roll_no"],
            address=student.get("address"),
            hostel=student.get("hostel"),
        )

    if worker:
        worker_detail = WorkerProfileDetail(
            employee_id=worker.get("employee_id"),
            zone=worker.get("zone"),
        )

    return ProfileResponse(
        id=profile["id"],
        user_id=profile["user_id"],
        name=profile["name"],
        role=profile["role"],
        phone=profile.get("phone"),
        created_at=profile["created_at"],
        student_detail=student_detail,
        worker_detail=worker_detail,
    )


async def get_profile_by_user_id(user_id: str) -> ProfileResponse:
    """Get full profile (base + role-specific) by auth user_id."""
    admin = get_supabase_admin()

    result = admin.table("profiles").select("*").eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    profile = result.data[0]
    return await _enrich_profile(profile)


async def get_profile_by_id(profile_id: str) -> ProfileResponse:
    """Get full profile by profile ID."""
    admin = get_supabase_admin()

    result = admin.table("profiles").select("*").eq("id", profile_id).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    profile = result.data[0]
    return await _enrich_profile(profile)


async def _enrich_profile(profile: dict) -> ProfileResponse:
    """Fetch role-specific data and build full response."""
    admin = get_supabase_admin()
    student = None
    worker = None

    if profile["role"] == "student":
        sp = admin.table("student_profiles").select("*").eq("profile_id", profile["id"]).execute()
        student = sp.data[0] if sp.data else None

    elif profile["role"] == "worker":
        wp = admin.table("worker_profiles").select("*").eq("profile_id", profile["id"]).execute()
        worker = wp.data[0] if wp.data else None

    return _build_profile_response(profile, student, worker)


async def list_workers() -> list[ProfileResponse]:
    """List all worker profiles (for admin assignment dropdown)."""
    admin = get_supabase_admin()

    result = admin.table("profiles").select("*").eq("role", "worker").execute()

    profiles = []
    for p in result.data:
        wp = admin.table("worker_profiles").select("*").eq("profile_id", p["id"]).execute()
        worker = wp.data[0] if wp.data else None
        profiles.append(_build_profile_response(p, None, worker))

    return profiles


async def update_profile(user: dict, data: UpdateProfileRequest) -> ProfileResponse:
    """Update the current user's profile (base + role-specific fields)."""
    admin = get_supabase_admin()
    profile_id = user["id"]

    # Update base profile fields
    base_updates = {}
    if data.name is not None:
        base_updates["name"] = data.name
    if data.phone is not None:
        base_updates["phone"] = data.phone

    if base_updates:
        admin.table("profiles").update(base_updates).eq("id", profile_id).execute()

    # Update role-specific fields
    if user["role"] == "student":
        student_updates = {}
        if data.roll_no is not None:
            student_updates["roll_no"] = data.roll_no
        if data.address is not None:
            student_updates["address"] = data.address
        if data.hostel is not None:
            student_updates["hostel"] = data.hostel

        if student_updates:
            admin.table("student_profiles").update(student_updates).eq("profile_id", profile_id).execute()

    elif user["role"] == "worker":
        worker_updates = {}
        if data.employee_id is not None:
            worker_updates["employee_id"] = data.employee_id
        if data.zone is not None:
            worker_updates["zone"] = data.zone

        if worker_updates:
            admin.table("worker_profiles").update(worker_updates).eq("profile_id", profile_id).execute()

    # Return updated profile
    return await get_profile_by_id(profile_id)
