"""File tools and Execution engine for Antigravity+ Web IDE.

Provides real file system manipulation, directory trees, file creation,
deletion, renaming, diffing, and real subprocess code execution.
"""

from __future__ import annotations

import difflib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class FileTools:
    """Core file manipulation and execution utilities for the web environment."""

    def __init__(self, workspace_root: str = ".") -> None:
        self.workspace_root = Path(workspace_root).resolve()

    def _resolve(self, rel_path: str) -> Path:
        p = Path(rel_path)
        if p.is_absolute():
            return p
        return (self.workspace_root / rel_path).resolve()

    def read_file(self, rel_path: str) -> Dict[str, Any]:
        """Read real content and line count of a file from disk."""
        target = self._resolve(rel_path)
        if not target.exists():
            return {"success": False, "error": f"File not found: {rel_path}"}
        try:
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return {
                "success": True,
                "file_path": rel_path,
                "content": content,
                "lines": len(content.splitlines()),
                "size_bytes": target.stat().st_size,
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def write_file(self, rel_path: str, content: str) -> Dict[str, Any]:
        """Write code content to real file on disk, creating parent directories as needed."""
        target = self._resolve(rel_path)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            return {
                "success": True,
                "file_path": rel_path,
                "bytes_written": len(content.encode("utf-8")),
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def create_file(self, rel_path: str, content: str = "") -> Dict[str, Any]:
        """Create a new file on disk."""
        target = self._resolve(rel_path)
        if target.exists():
            return {"success": False, "error": f"File already exists: {rel_path}"}
        return self.write_file(rel_path, content)

    def create_directory(self, rel_path: str) -> Dict[str, Any]:
        """Create a new directory on disk."""
        target = self._resolve(rel_path)
        try:
            target.mkdir(parents=True, exist_ok=True)
            return {"success": True, "path": rel_path}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def delete_item(self, rel_path: str) -> Dict[str, Any]:
        """Delete a file or folder from disk."""
        target = self._resolve(rel_path)
        if not target.exists():
            return {"success": False, "error": f"Path does not exist: {rel_path}"}
        try:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            return {"success": True, "path": rel_path}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def rename_item(self, old_path: str, new_path: str) -> Dict[str, Any]:
        """Rename or move a file or folder."""
        src = self._resolve(old_path)
        dest = self._resolve(new_path)
        if not src.exists():
            return {"success": False, "error": f"Source does not exist: {old_path}"}
        if dest.exists():
            return {"success": False, "error": f"Destination already exists: {new_path}"}
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dest)
            return {"success": True, "old_path": old_path, "new_path": new_path}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def move_item(self, src_path: str, dest_folder: str) -> Dict[str, Any]:
        """Move a file or directory into a target directory (drag-and-drop)."""
        src = self._resolve(src_path)
        dest_dir = self._resolve(dest_folder)
        if not src.exists():
            return {"success": False, "error": f"Source does not exist: {src_path}"}
        if not dest_dir.exists() or not dest_dir.is_dir():
            return {"success": False, "error": f"Target directory does not exist: {dest_folder}"}
        try:
            target = dest_dir / src.name
            if target.exists():
                return {"success": False, "error": f"An item named {src.name} already exists in {dest_folder}"}
            shutil.move(str(src), str(target))
            rel_new = str(target.relative_to(self.workspace_root)).replace("\\", "/")
            return {"success": True, "old_path": src_path, "new_path": rel_new}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def clear_caches(self) -> Dict[str, Any]:
        """Wipe temporary cache folders for a clean reset state."""
        wiped = []
        for root, dirs, _ in os.walk(self.workspace_root, topdown=False):
            for d in list(dirs):
                if d in ("__pycache__", ".pytest_cache"):
                    p = Path(root) / d
                    try:
                        shutil.rmtree(p, ignore_errors=True)
                        wiped.append(d)
                    except Exception:
                        pass
        return {"success": True, "wiped_count": len(wiped), "cleared_directories": wiped}

    def replace_content(self, rel_path: str, target_text: str, replacement_text: str) -> Dict[str, Any]:
        """Replace exact target string with replacement."""
        res = self.read_file(rel_path)
        if not res["success"]:
            return res
        current = res["content"]
        if target_text not in current:
            return {"success": False, "error": "Target content string not found in file."}
        updated = current.replace(target_text, replacement_text, 1)
        return self.write_file(rel_path, updated)

    def get_hierarchical_tree(self, sub_dir: str = ".") -> Dict[str, Any]:
        """Generate nested tree structure with files and folders for VS Code explorer."""
        base = self._resolve(sub_dir)

        def _build_node(path: Path) -> Dict[str, Any]:
            rel = str(path.relative_to(self.workspace_root)).replace("\\", "/")
            is_dir = path.is_dir()
            node: Dict[str, Any] = {
                "name": path.name,
                "path": rel,
                "is_dir": is_dir,
            }
            if is_dir:
                children = []
                try:
                    for child in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                        if child.name.startswith(".") and child.name not in (".env",):
                            continue
                        if child.name in ("__pycache__", "node_modules", ".pytest_cache", ".git"):
                            continue
                        children.append(_build_node(child))
                except Exception:
                    pass
                node["children"] = children
            else:
                node["size"] = path.stat().st_size
                node["extension"] = path.suffix.lower()
            return node

        tree = _build_node(base)
        return {"success": True, "tree": tree.get("children", [])}

    def list_files(self, sub_dir: str = ".") -> Dict[str, Any]:
        """Produce flat list of files for explorer backwards compatibility."""
        base = self._resolve(sub_dir)
        files_list = []
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__")]
            rel_dir = os.path.relpath(root, self.workspace_root).replace("\\", "/")
            for f in sorted(files):
                if f.startswith("."):
                    continue
                rel_file = f if rel_dir == "." else f"{rel_dir}/{f}"
                files_list.append({"name": f, "path": rel_file, "is_dir": False})
        return {"success": True, "files": files_list, "total": len(files_list)}

    def execute_code(self, rel_path: str) -> Dict[str, Any]:
        """Execute a real Python script on disk and capture real stdout/stderr/runtime."""
        target = self._resolve(rel_path)
        if not target.exists():
            return {"success": False, "error": f"File not found: {rel_path}"}

        start_time = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, str(target)],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=60,
            )
            duration = round(time.time() - start_time, 3)
            return {
                "success": proc.returncode == 0,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "exit_code": proc.returncode,
                "execution_time_seconds": duration,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Execution timed out after 60 seconds", "exit_code": -1}
        except Exception as exc:
            return {"success": False, "error": str(exc), "exit_code": 1}

    def run_shell_command(self, command: str) -> Dict[str, Any]:
        """Run an arbitrary terminal command in the workspace directory."""
        start_time = time.time()
        try:
            proc = subprocess.run(
                command,
                cwd=str(self.workspace_root),
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
            duration = round(time.time() - start_time, 3)
            return {
                "success": proc.returncode == 0,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "exit_code": proc.returncode,
                "execution_time_seconds": duration,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out after 60s", "exit_code": -1}
        except Exception as exc:
            return {"success": False, "error": str(exc), "exit_code": 1}

    def compute_diff(self, original_text: str, modified_text: str, filename: str = "file") -> str:
        """Generate unified diff between original and modified versions."""
        orig_lines = original_text.splitlines(keepends=True)
        mod_lines = modified_text.splitlines(keepends=True)
        diff = difflib.unified_diff(orig_lines, mod_lines, fromfile=f"a/{filename}", tofile=f"b/{filename}")
        return "".join(diff)
