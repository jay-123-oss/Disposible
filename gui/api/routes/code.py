"""Code API routes for browsing workspace files, reading file contents, and saving edits."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/code", tags=["Code"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class FileSaveRequest(BaseModel):
    content: str


@router.get("/files")
def list_files() -> Dict[str, Any]:
    """List code files in workspace."""
    allowed_exts = {".py", ".yaml", ".yml", ".md", ".txt", ".json", ".html", ".css", ".js"}
    file_list: List[str] = []

    for root, _, files in os.walk(str(BASE_DIR)):
        rel_root = os.path.relpath(root, str(BASE_DIR))
        if any(part.startswith(".") or part in ("__pycache__", "venv", "node_modules") for part in Path(rel_root).parts):
            continue
        for file in files:
            p = Path(file)
            if p.suffix in allowed_exts:
                full_rel = os.path.normpath(os.path.join(rel_root, file)).replace("\\", "/")
                file_list.append(full_rel)

    return {"total": len(file_list), "files": sorted(file_list[:100])}


@router.get("/file/{path:path}")
def get_file_content(path: str) -> Dict[str, Any]:
    """Read contents of a specific file."""
    target = (BASE_DIR / path).resolve()
    if not str(target).startswith(str(BASE_DIR)):
        raise HTTPException(status_code=403, detail="Path traversal forbidden")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        content = target.read_text(encoding="utf-8")
        return {"path": path, "size": len(content), "content": content}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/file/{path:path}")
def save_file_content(path: str, req: FileSaveRequest) -> Dict[str, Any]:
    """Save updated content to a file."""
    target = (BASE_DIR / path).resolve()
    if not str(target).startswith(str(BASE_DIR)):
        raise HTTPException(status_code=403, detail="Path traversal forbidden")

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(req.content, encoding="utf-8")
        return {"status": "SUCCESS", "path": path, "bytes_written": len(req.content)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
