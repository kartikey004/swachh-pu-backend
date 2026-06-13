"""
Task router — CRUD + lifecycle transitions (create, assign, reject, complete).
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user, require_role
from app.models.task import (
    TaskCreateRequest,
    TaskResponse,
    TaskListResponse,
    TaskAssignRequest,
    TaskStatusResponse,
)
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    data: TaskCreateRequest,
    user: dict = Depends(get_current_user),
):
    """
    Create a new task / complaint.

    **Flow**: Upload photo (and optionally audio) via `/upload/photo` first,
    then call this endpoint with the returned URL + lat/long + description.

    The task starts with status `pending`.
    """
    return await task_service.create_task(data, user["id"])


@router.get("/my-tasks", response_model=list[TaskResponse])
async def get_my_tasks(user: dict = Depends(require_role("worker"))):
    """
    Get all tasks assigned to the current worker.

    **Worker only**.
    """
    return await task_service.get_my_tasks(user["id"])


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status: pending, assigned, completed, rejected"),
    profile_id: Optional[str] = Query(None, description="Filter by creator profile ID"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned worker profile ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    """
    List tasks with optional filters and pagination.

    - **Students** see their own created tasks.
    - **Workers** see their assigned tasks.
    - **Admins** see all tasks.
    """
    # Scope the query based on role
    if user["role"] == "student":
        profile_id = user["id"]  # Students can only see own tasks
    elif user["role"] == "worker":
        assigned_to = user["id"]  # Workers see assigned tasks

    # Admins see everything (no filter override)

    tasks, total = await task_service.list_tasks(
        status_filter=status,
        profile_id=profile_id,
        assigned_to=assigned_to,
        limit=limit,
        offset=offset,
    )

    return TaskListResponse(tasks=tasks, count=total)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, user: dict = Depends(get_current_user)):
    """Get a single task by ID."""
    return await task_service.get_task(task_id)


@router.patch("/{task_id}/assign", response_model=TaskStatusResponse)
async def assign_task(
    task_id: str,
    data: TaskAssignRequest,
    user: dict = Depends(require_role("admin")),
):
    """
    Assign a pending task to a worker.

    **Admin only**. Changes status from `pending` → `assigned`.
    """
    return await task_service.assign_task(task_id, str(data.worker_profile_id))


@router.patch("/{task_id}/reject", response_model=TaskStatusResponse)
async def reject_task(
    task_id: str,
    user: dict = Depends(require_role("admin")),
):
    """
    Reject a pending task.

    **Admin only**. Changes status from `pending` → `rejected`.
    """
    return await task_service.reject_task(task_id)


@router.patch("/{task_id}/complete", response_model=TaskStatusResponse)
async def complete_task(
    task_id: str,
    user: dict = Depends(require_role("worker")),
):
    """
    Mark an assigned task as completed.

    **Worker only**. Can only complete tasks assigned to you.
    Changes status from `assigned` → `completed`.
    """
    return await task_service.complete_task(task_id, user["id"])
