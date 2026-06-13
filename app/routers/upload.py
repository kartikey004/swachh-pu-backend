"""
Upload router — file uploads to Supabase Storage.
"""

from fastapi import APIRouter, Depends, UploadFile, File

from app.dependencies import get_current_user
from app.services import storage_service

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/photo")
async def upload_photo(
    file: UploadFile = File(..., description="Photo file (JPEG, PNG, WebP, HEIC — max 10 MB)"),
    user: dict = Depends(get_current_user),
):
    """
    Upload a task photo to Supabase Storage.

    Returns the public URL. Use this URL in the `POST /tasks/` request body.
    """
    url = await storage_service.upload_photo(file)
    return {"photo_url": url, "message": "Photo uploaded successfully"}


@router.post("/audio")
async def upload_audio(
    file: UploadFile = File(..., description="Audio file (MP3, WAV, OGG, AAC, M4A — max 25 MB)"),
    user: dict = Depends(get_current_user),
):
    """
    Upload a task audio recording to Supabase Storage.

    Returns the public URL. Use this URL in the `POST /tasks/` request body.
    """
    url = await storage_service.upload_audio(file)
    return {"audio_url": url, "message": "Audio uploaded successfully"}
