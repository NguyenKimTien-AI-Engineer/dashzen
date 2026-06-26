from __future__ import annotations

import uuid

from agents.streaming.rate_limit import check_rate_limit, get_bucket_config, retry_after_seconds
from core.security.paths import has_path_separator, sanitize_filename
from db.models.user import User
from db.services.file_service import save_upload
from db.session import get_db
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, require_task
from api.schemas.gates import UploadResponse

router = APIRouter(prefix="/v1/tasks", tags=["upload"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_MIME = {
    "text/csv",
    "application/json",
    "image/png",
    "image/jpeg",
    "application/pdf",
}


@router.post("/{task_id}/upload", response_model=UploadResponse, status_code=201)
async def upload_file(
    task_id: uuid.UUID,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    limit, window = get_bucket_config("upload")
    if not await check_rate_limit("upload", str(user.id), limit, window):
        retry = await retry_after_seconds("upload", str(user.id), window)
        raise HTTPException(
            status_code=429,
            detail="Upload rate limit exceeded",
            headers={
                "Retry-After": str(retry),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
            },
        )

    await require_task(task_id, user, db)

    raw_name = file.filename or "upload"
    if has_path_separator(raw_name):
        raise HTTPException(status_code=400, detail="Invalid filename")

    name = sanitize_filename(raw_name)
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail=f"Unsupported content type: {content_type}")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 10MB limit")

    saved = await save_upload(
        db,
        task_id=task_id,
        name=name,
        content=data,
        content_type=content_type,
        size=len(data),
    )
    await db.commit()
    return UploadResponse(
        id=saved.id,
        name=saved.name,
        source=saved.source,
        kind=saved.kind,
        size=saved.size,
        content_type=saved.content_type,
    )
