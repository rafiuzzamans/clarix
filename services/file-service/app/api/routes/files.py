import os
import uuid

import aiofiles
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db

router = APIRouter(prefix="/files", tags=["Files"])

STORAGE_PATH = os.getenv("FILE_STORAGE_PATH", "/app/storage")
MAX_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB

ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf",
    "text/plain", "text/csv",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/zip",
}


def _get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


@router.post("/upload", summary="Upload a file attachment")
async def upload_file(
    file: UploadFile = File(...),
    case_id: Optional[str] = Form(None),
    uploader_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    # Validate mime type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"File type '{file.content_type}' is not allowed")

    # Read and validate size
    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 20MB limit")

    # Generate safe storage path
    file_id = str(uuid.uuid4())
    ext = _get_extension(file.filename or "file.bin")
    storage_filename = f"{file_id}{ext}"
    storage_dir = os.path.join(STORAGE_PATH, "attachments")
    os.makedirs(storage_dir, exist_ok=True)
    storage_full_path = os.path.join(storage_dir, storage_filename)

    # Write file
    async with aiofiles.open(storage_full_path, "wb") as f:
        await f.write(content)

    # Persist record
    await db.execute(text("""
        INSERT INTO file_attachments
            (id, case_id, uploader_id, filename, original_name, mime_type, size_bytes, storage_path)
        VALUES
            (:id, :case_id, :uploader_id, :filename, :original_name, :mime_type, :size_bytes, :storage_path)
    """), {
        "id": file_id,
        "case_id": case_id,
        "uploader_id": uploader_id,
        "filename": storage_filename,
        "original_name": file.filename,
        "mime_type": file.content_type,
        "size_bytes": len(content),
        "storage_path": storage_full_path,
    })
    await db.commit()

    return {
        "file_id": file_id,
        "filename": storage_filename,
        "original_name": file.filename,
        "size_bytes": len(content),
        "mime_type": file.content_type,
        "case_id": case_id,
    }


@router.get("/download/{file_id}", summary="Download a file")
async def download_file(file_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("SELECT * FROM file_attachments WHERE id = :id AND is_deleted = FALSE"),
        {"id": file_id}
    )
    row = result.mappings().one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="File not found")

    if not os.path.exists(row["storage_path"]):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=row["storage_path"],
        filename=row["original_name"],
        media_type=row["mime_type"],
    )


@router.get("/case/{case_id}", summary="List files for a case")
async def list_case_files(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        text("""
        SELECT id, filename, original_name, mime_type, size_bytes, created_at
        FROM file_attachments
        WHERE case_id = :case_id AND is_deleted = FALSE
        ORDER BY created_at DESC
        """),
        {"case_id": case_id}
    )
    return {"files": [dict(r) for r in result.mappings().all()]}


@router.delete("/{file_id}", summary="Soft-delete a file")
async def delete_file(file_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(
        text("UPDATE file_attachments SET is_deleted = TRUE WHERE id = :id"),
        {"id": file_id}
    )
    await db.commit()
    return {"status": "deleted", "file_id": file_id}

