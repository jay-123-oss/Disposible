"""File operations tools with safety classification and diff tracking."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.tools.base import BaseTool, SafetyLevel, ToolResult


class ListFilesTool(BaseTool):
    name = "list_files"
    description = "List files and directories in a given path (recursively or shallow)."
    safety_level = SafetyLevel.SAFE

    def _run(self, directory: str = ".", recursive: bool = False, max_depth: int = 2) -> ToolResult:
        dir_path = Path(directory).resolve()
        if not dir_path.exists():
            return ToolResult(success=False, output=[], error=f"Directory not found: {directory}")

        entries: List[Dict[str, Any]] = []
        try:
            if recursive:
                for root, dirs, files in os.walk(dir_path):
                    rel_root = Path(root).relative_to(dir_path)
                    depth = len(rel_root.parts)
                    if depth > max_depth:
                        continue
                    # Skip noise directories
                    dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".pytest_cache"}]
                    for f in files:
                        rel_path = (rel_root / f).as_posix() if str(rel_root) != "." else f
                        entries.append({"path": rel_path, "type": "file"})
                    for d in dirs:
                        rel_path = (rel_root / d).as_posix() if str(rel_root) != "." else d
                        entries.append({"path": rel_path, "type": "directory"})
            else:
                for item in dir_path.iterdir():
                    if item.name.startswith((".git", "__pycache__")):
                        continue
                    entries.append({"path": item.name, "type": "directory" if item.is_dir() else "file"})

            return ToolResult(success=True, output=entries, stdout=f"Found {len(entries)} items.")
        except Exception as e:
            return ToolResult(success=False, output=[], error=str(e))


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read file content with line numbers and slice support."
    safety_level = SafetyLevel.SAFE

    def _run(self, filepath: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> ToolResult:
        path = Path(filepath).resolve()
        if not path.is_file():
            return ToolResult(success=False, output=None, error=f"File not found: {filepath}")

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            total_lines = len(lines)

            s = max(1, start_line) - 1 if start_line else 0
            e = min(total_lines, end_line) if end_line else total_lines

            sliced_lines = lines[s:e]
            formatted_content = "\n".join(f"{i + s + 1}: {line}" for i, line in enumerate(sliced_lines))

            return ToolResult(
                success=True,
                output={
                    "filepath": str(path),
                    "total_lines": total_lines,
                    "content": "\n".join(sliced_lines),
                    "formatted": formatted_content,
                },
                stdout=f"Read {len(sliced_lines)} lines from {filepath}",
            )
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write complete content to a file. Overwrites if exists."
    safety_level = SafetyLevel.CAUTION

    def _run(self, filepath: str, content: str) -> ToolResult:
        path = Path(filepath).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        old_content = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        old_lines = len(old_content.splitlines()) if old_content else 0
        new_lines = len(content.splitlines()) if content else 0

        path.write_text(content, encoding="utf-8")

        lines_added = max(0, new_lines - old_lines) if old_lines else new_lines
        lines_removed = max(0, old_lines - new_lines) if old_lines else 0

        return ToolResult(
            success=True,
            output={"filepath": str(path), "bytes_written": len(content)},
            stdout=f"Wrote {len(content)} bytes to {filepath}",
            metadata={
                "lines_added": lines_added,
                "lines_removed": lines_removed,
                "is_new_file": old_lines == 0,
            },
        )


class EditFileTool(BaseTool):
    name = "edit_file"
    description = "Apply a targeted replacement or patch to an existing file."
    safety_level = SafetyLevel.CAUTION

    def _run(self, filepath: str, old_snippet: str, new_snippet: str) -> ToolResult:
        path = Path(filepath).resolve()
        if not path.is_file():
            return ToolResult(success=False, output=None, error=f"File not found: {filepath}")

        content = path.read_text(encoding="utf-8")
        if old_snippet not in content:
            return ToolResult(
                success=False,
                output=None,
                error="Target snippet to replace was not found in the file.",
            )

        occurrences = content.count(old_snippet)
        if occurrences > 1:
            return ToolResult(
                success=False,
                output=None,
                error=f"Target snippet appears {occurrences} times. Must be unique to edit safely.",
            )

        new_content = content.replace(old_snippet, new_snippet, 1)
        path.write_text(new_content, encoding="utf-8")

        return ToolResult(
            success=True,
            output={"filepath": str(path), "modified": True},
            stdout=f"Successfully updated snippet in {filepath}",
        )


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Delete a file or directory permanently."
    safety_level = SafetyLevel.DANGEROUS

    def _run(self, filepath: str, force: bool = False) -> ToolResult:
        path = Path(filepath).resolve()
        if not path.exists():
            return ToolResult(success=False, output=None, error=f"Path does not exist: {filepath}")

        if not force:
            return ToolResult(
                success=False,
                output=None,
                error="Delete operation blocked: DANGEROUS level requires explicit user confirmation or force=True.",
                safety_level=SafetyLevel.DANGEROUS,
            )

        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

        return ToolResult(
            success=True,
            output={"deleted": str(path)},
            stdout=f"Deleted {filepath}",
            safety_level=SafetyLevel.DANGEROUS,
        )
