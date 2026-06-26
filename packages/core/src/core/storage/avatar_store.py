from __future__ import annotations

from pathlib import Path
from uuid import UUID

from core.config import get_settings

MAX_AVATAR_BYTES = 2 * 1024 * 1024
ALLOWED_AVATAR_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _storage_root() -> Path:
    root = Path(get_settings().avatar_storage_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def detect_image_content_type(data: bytes) -> str | None:
    if len(data) >= 3 and data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if len(data) >= 8 and data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def avatar_file_path(user_id: UUID, ext: str) -> Path:
    return _storage_root() / f"{user_id}{ext}"


def save_avatar_file(user_id: UUID, data: bytes, content_type: str) -> str:
    ext = ALLOWED_AVATAR_MIME.get(content_type)
    if ext is None:
        raise ValueError(f"Unsupported avatar content type: {content_type}")

    detected = detect_image_content_type(data)
    if detected is None or detected != content_type:
        raise ValueError("Avatar file content does not match declared image type")

    if len(data) > MAX_AVATAR_BYTES:
        raise ValueError("Avatar exceeds 2MB limit")

    delete_avatar_file(user_id)
    key = f"{user_id}{ext}"
    path = _storage_root() / key
    path.write_bytes(data)
    return key


def read_avatar_file(stored_name: str) -> tuple[bytes, str]:
    path = _storage_root() / stored_name
    if not path.is_file():
        raise FileNotFoundError(stored_name)

    data = path.read_bytes()
    content_type = detect_image_content_type(data) or "application/octet-stream"
    return data, content_type


def delete_avatar_file(user_id: UUID, stored_name: str | None = None) -> None:
    root = _storage_root()
    if stored_name:
        path = root / stored_name
        if path.is_file():
            path.unlink()
        return

    for ext in ALLOWED_AVATAR_MIME.values():
        path = avatar_file_path(user_id, ext)
        if path.is_file():
            path.unlink()
