from __future__ import annotations

import io
import uuid
import zipfile

from core.schemas.dashboard_spec import validate_export_files
from db.models.user import User
from db.services.file_service import get_artifacts
from db.services.task_service import get_task
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user

router = APIRouter(prefix="/v1/tasks", tags=["export"])


@router.get("/{task_id}/export/zip")
async def export_task_zip(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    task = await get_task(db, task_id, user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    files = await get_artifacts(db, task_id)
    workspace_files = [f for f in files if f.source in ("workspace", "upload")]

    file_contents: dict[str, str] = {}
    for f in workspace_files:
        if f.content is not None:
            file_contents[f.name] = f.content

    try:
        validate_export_files(file_contents)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in workspace_files:
            if f.content is not None:
                zf.writestr(f.name, f.content)
            elif f.url:
                zf.writestr(f.name, f"[binary at {f.url}]")

    buffer.seek(0)
    filename = f"task-{task_id}.zip"
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
