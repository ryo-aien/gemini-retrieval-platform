"""File storage utilities"""
import os
import uuid
import aiofiles
from pathlib import Path
from typing import Dict


# Supported MIME types
SUPPORTED_MIME_TYPES = {
    "application/pdf": [".pdf"],
    "text/markdown": [".md", ".markdown"],
    "text/plain": [".txt"],
}


def get_temp_dir() -> Path:
    """Get temporary directory path"""
    temp_dir = Path("/app/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def get_data_dir() -> Path:
    """Get data directory path"""
    data_dir = Path("/app/data")
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def validate_file_type(filename: str, mime_type: str) -> bool:
    """Validate file type against supported MIME types"""
    file_ext = Path(filename).suffix.lower()

    for supported_mime, extensions in SUPPORTED_MIME_TYPES.items():
        if mime_type == supported_mime or mime_type.startswith(supported_mime):
            return file_ext in extensions

    return False


def get_mime_type_from_filename(filename: str) -> str:
    """Get MIME type from filename extension"""
    file_ext = Path(filename).suffix.lower()

    for mime_type, extensions in SUPPORTED_MIME_TYPES.items():
        if file_ext in extensions:
            return mime_type

    return "application/octet-stream"


async def save_upload_file(file, max_size: int = 10 * 1024 * 1024) -> Dict[str, str]:
    """Save uploaded file to temporary directory"""
    # Generate unique filename
    file_id = str(uuid.uuid4())
    original_filename = file.filename
    file_ext = Path(original_filename).suffix
    temp_filename = f"{file_id}{file_ext}"

    temp_dir = get_temp_dir()
    temp_path = temp_dir / temp_filename

    # Read file content
    content = await file.read()

    # Check file size
    if len(content) > max_size:
        raise ValueError(f"File size exceeds maximum allowed size of {max_size} bytes")

    # Save file
    async with aiofiles.open(temp_path, "wb") as f:
        await f.write(content)

    return {
        "file_id": file_id,
        "original_filename": original_filename,
        "temp_path": str(temp_path),
        "size": len(content),
        "mime_type": get_mime_type_from_filename(original_filename)
    }


async def delete_temp_file(file_path: str) -> bool:
    """Delete a temporary file"""
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()
            return True
        return False
    except Exception:
        return False


def cleanup_temp_files(max_age_hours: int = 24):
    """Clean up old temporary files"""
    import time

    temp_dir = get_temp_dir()
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600

    for file_path in temp_dir.glob("*"):
        if file_path.is_file():
            file_age = current_time - file_path.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    file_path.unlink()
                except Exception:
                    pass
