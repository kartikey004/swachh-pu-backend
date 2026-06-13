"""
Task service — Supabase queries for task CRUD and status transitions.
"""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status

from app.models.task import TaskCreateRequest, TaskResponse, TaskStatusResponse
from app.utils.supabase_client import get_supabase_admin


def _row_to_response(row: dict) -> TaskResponse:
    """Convert a raw DB row to TaskResponse."""
    return TaskResponse(
        id=row["id"],
        photo_url=row["photo_url"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        audio_url=row.get("audio_url"),
        description=row["description"],
        profile_id=row["profile_id"],
        assigned_to=row.get("assigned_to"),
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        creator_name=row.get("creator_name"),
        assignee_name=row.get("assignee_name"),
    )


async def create_task(data: TaskCreateRequest, profile_id: str) -> TaskResponse:
    """Create a new task (status defaults to 'pending')."""
    admin = get_supabase_admin()

    task_data = {
        "photo_url": data.photo_url,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "audio_url": data.audio_url,
        "description": data.description,
        "profile_id": profile_id,
        "status": "pending",
    }

    try:
        result = admin.table("tasks").insert(task_data).execute()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(exc)}",
        )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task creation returned no data",
        )

    return _row_to_response(result.data[0])


async def get_task(task_id: str) -> TaskResponse:
    """Get a single task by ID."""
    admin = get_supabase_admin()

    result = admin.table("tasks").select("*").eq("id", task_id).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    task = result.data[0]

    # Enrich with creator name
    creator_result = admin.table("profiles").select("name").eq("id", task["profile_id"]).execute()
    if creator_result.data:
        task["creator_name"] = creator_result.data[0]["name"]

    # Enrich with assignee name
    if task.get("assigned_to"):
        assignee_result = admin.table("profiles").select("name").eq("id", task["assigned_to"]).execute()
        if assignee_result.data:
            task["assignee_name"] = assignee_result.data[0]["name"]

    return _row_to_response(task)


async def list_tasks(
    status_filter: Optional[str] = None,
    profile_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[TaskResponse], int]:
    """
    List tasks with optional filters.
    Returns (tasks, total_count).
    """
    admin = get_supabase_admin()

    query = admin.table("tasks").select("*", count="exact")

    if status_filter:
        query = query.eq("status", status_filter)
    if profile_id:
        query = query.eq("profile_id", profile_id)
    if assigned_to:
        query = query.eq("assigned_to", assigned_to)

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    tasks = [_row_to_response(row) for row in result.data]
    total = result.count if result.count is not None else len(tasks)

    return tasks, total


async def get_my_tasks(profile_id: str) -> list[TaskResponse]:
    """Get tasks assigned to a specific worker."""
    admin = get_supabase_admin()

    result = (
        admin.table("tasks")
        .select("*")
        .eq("assigned_to", profile_id)
        .order("created_at", desc=True)
        .execute()
    )

    return [_row_to_response(row) for row in result.data]


async def assign_task(task_id: str, worker_profile_id: str) -> TaskStatusResponse:
    """Assign a pending task to a worker (admin action)."""
    admin = get_supabase_admin()

    # Verify task exists and is in valid state
    task = await get_task(task_id)
    if task.status not in ("pending",):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot assign a task with status '{task.status}'. Only 'pending' tasks can be assigned.",
        )

    # Verify worker exists and is actually a worker
    worker_result = admin.table("profiles").select("*").eq("id", worker_profile_id).execute()
    if not worker_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")
    if worker_result.data[0]["role"] != "worker":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected profile is not a worker")

    # Update task
    admin.table("tasks").update({
        "assigned_to": worker_profile_id,
        "status": "assigned",
    }).eq("id", task_id).execute()

    return TaskStatusResponse(task_id=task_id, new_status="assigned", message="Task assigned to worker")


async def reject_task(task_id: str) -> TaskStatusResponse:
    """Reject a pending task (admin action)."""
    admin = get_supabase_admin()

    task = await get_task(task_id)
    if task.status not in ("pending",):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject a task with status '{task.status}'. Only 'pending' tasks can be rejected.",
        )

    admin.table("tasks").update({"status": "rejected"}).eq("id", task_id).execute()

    return TaskStatusResponse(task_id=task_id, new_status="rejected", message="Task rejected")


async def complete_task(task_id: str, worker_profile_id: str) -> TaskStatusResponse:
    """Mark an assigned task as completed (worker action)."""
    admin = get_supabase_admin()

    task = await get_task(task_id)
    if task.status != "assigned":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete a task with status '{task.status}'. Only 'assigned' tasks can be completed.",
        )

    # Ensure the worker completing is the one assigned
    if str(task.assigned_to) != worker_profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only complete tasks assigned to you",
        )

    admin.table("tasks").update({"status": "completed"}).eq("id", task_id).execute()

    return TaskStatusResponse(task_id=task_id, new_status="completed", message="Task completed")
