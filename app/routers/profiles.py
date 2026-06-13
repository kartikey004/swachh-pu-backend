"""
Profile router — CRUD operations on user profiles.
"""

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, require_role
from app.models.profile import ProfileResponse, ProfileListResponse, UpdateProfileRequest
from app.services import profile_service

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(user: dict = Depends(get_current_user)):
    """Get the current user's full profile (base + student/worker details)."""
    return await profile_service.get_profile_by_id(user["id"])


@router.put("/me", response_model=ProfileResponse)
async def update_my_profile(
    data: UpdateProfileRequest,
    user: dict = Depends(get_current_user),
):
    """Update the current user's profile. Only non-null fields are updated."""
    return await profile_service.update_profile(user, data)


@router.get("/workers", response_model=ProfileListResponse)
async def list_workers(user: dict = Depends(require_role("admin"))):
    """
    List all worker profiles.

    **Admin only** — used to populate the worker dropdown when assigning tasks.
    """
    workers = await profile_service.list_workers()
    return ProfileListResponse(profiles=workers, count=len(workers))


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: str, user: dict = Depends(require_role("admin"))):
    """
    Get any profile by ID.

    **Admin only**.
    """
    return await profile_service.get_profile_by_id(profile_id)
