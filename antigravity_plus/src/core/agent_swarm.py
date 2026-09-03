"""Agent Swarm: Parallel Multi-Agent Missions and Dynamic Subagent Spawning.

Features:
- Mission-Based Swarms (Frontend, Backend, QA, Security, Infrastructure in parallel)
- Dynamic Subagent Spawning (invoke_subagent mechanism with parent-child tracking)
- Context-Lean Handoffs (Structured compact handoff payloads to avoid token blowup)
- Isolated Workspace Modes (inherit, branch, share)
- Massive Parallelism (Scales up to 93+ concurrent subagents)
"""

from __future__ import annotations

import concurrent.futures
import logging
import os
import shutil
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("AntigravityPlus.AgentSwarm")


class WorkspaceMode(str, Enum):
    INHERIT = "inherit"  # Operates directly in current workspace directory
    BRANCH = "branch"    # Operates in an isolated copy / sandbox directory
    SHARE = "share"      # Operates in shared team directory


@dataclass
class HandoffPayload:
    """Context-lean structured summary returned when a subagent finishes."""
    subagent_id: str
    parent_id: Optional[str]
    role: str
    status: str
    summary: str
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    execution_time_seconds: float = 0.0


@dataclass
class SwarmMember:
    """Represents an active agent worker within the swarm."""
    agent_id: str
    role: str  # frontend, backend, qa, security, devops, etc.
    parent_id: Optional[str] = None
    workspace_mode: WorkspaceMode = WorkspaceMode.INHERIT
    sandbox_path: Optional[str] = None
    status: str = "IDLE"  # IDLE, RUNNING, COMPLETED, FAILED


class AgentSwarmCoordinator:
    """Coordinates parallel missions, dynamic subagent spawning, and lean handoffs."""

    def __init__(self, workspace_root: str = ".", max_workers: int = 93) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.active_swarms: Dict[str, List[SwarmMember]] = {}
        self.subagent_registry: Dict[str, SwarmMember] = {}
        self.sandboxes: List[str] = []

    def spawn_workspace(self, mode: WorkspaceMode, source_dir: Optional[str] = None) -> str:
        """Create workspace directory based on isolated workspace mode."""
        src = Path(source_dir or self.workspace_root)
        if mode == WorkspaceMode.INHERIT or mode == WorkspaceMode.SHARE:
            return str(src)

        # BRANCH mode creates an isolated sandboxed copy
        temp_dir = tempfile.mkdtemp(prefix="antigravity_branch_")
        self.sandboxes.append(temp_dir)
        try:
            # Copy source code files ignoring pycache, git, node_modules
            shutil.copytree(
                src,
                temp_dir,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", ".pytest_cache"),
            )
        except Exception as exc:
            logger.warning("Could not copy full workspace to branch: %s", exc)
        return temp_dir

    def invoke_subagent(
        self,
        role: str,
        task_prompt: str,
        parent_id: Optional[str] = None,
        workspace_mode: WorkspaceMode = WorkspaceMode.INHERIT,
        worker_func: Optional[Callable[[str, str], Dict[str, Any]]] = None,
    ) -> HandoffPayload:
        """Dynamically spawn a child subagent with isolated scope and lean handoff."""
        subagent_id = f"sub-{role}-{uuid.uuid4().hex[:6]}"
        sandbox = self.spawn_workspace(workspace_mode)

        member = SwarmMember(
            agent_id=subagent_id,
            role=role,
            parent_id=parent_id,
            workspace_mode=workspace_mode,
            sandbox_path=sandbox,
            status="RUNNING",
        )
        self.subagent_registry[subagent_id] = member

        start_time = time.time()
        logger.info("Spawning subagent %s (Role: %s, Mode: %s)", subagent_id, role, workspace_mode)

        result: Dict[str, Any] = {}
        try:
            if worker_func:
                result = worker_func(task_prompt, sandbox)
            else:
                result = {
                    "summary": f"Completed subagent task for {role}",
                    "files_modified": [],
                    "artifacts": {"task": task_prompt},
                }
            member.status = "COMPLETED"
        except Exception as exc:
            logger.exception("Subagent %s failed: %s", subagent_id, exc)
            member.status = "FAILED"
            result = {"summary": f"Error: {exc}", "files_modified": [], "artifacts": {}}

        latency = round(time.time() - start_time, 3)

        # Build context-lean handoff
        handoff = HandoffPayload(
            subagent_id=subagent_id,
            parent_id=parent_id,
            role=role,
            status=member.status,
            summary=result.get("summary", "Done"),
            files_created=result.get("files_created", []),
            files_modified=result.get("files_modified", []),
            artifacts=result.get("artifacts", {}),
            execution_time_seconds=latency,
        )
        return handoff

    def launch_mission(
        self,
        mission_name: str,
        roles: List[str],
        task_prompts: Dict[str, str],
        worker_func: Callable[[str, str, str], Dict[str, Any]],
        workspace_mode: WorkspaceMode = WorkspaceMode.INHERIT,
    ) -> Dict[str, Any]:
        """Launch parallel mission across multiple swarm roles."""
        mission_id = f"msn-{uuid.uuid4().hex[:8]}"
        logger.info("Launching Swarm Mission: '%s' [%s] with %d roles", mission_name, mission_id, len(roles))

        start_time = time.time()
        futures: Dict[concurrent.futures.Future, str] = {}

        for role in roles:
            prompt = task_prompts.get(role, f"Execute mission role {role} for {mission_name}")
            fut = self.executor.submit(
                self.invoke_subagent,
                role=role,
                task_prompt=prompt,
                parent_id=mission_id,
                workspace_mode=workspace_mode,
                worker_func=lambda p, s, r=role: worker_func(r, p, s),
            )
            futures[fut] = role

        handoffs: Dict[str, HandoffPayload] = {}
        for fut in concurrent.futures.as_completed(futures):
            role = futures[fut]
            try:
                handoff = fut.result()
                handoffs[role] = handoff
            except Exception as exc:
                logger.error("Role %s in mission %s threw an exception: %s", role, mission_id, exc)

        total_time = round(time.time() - start_time, 3)
        return {
            "mission_id": mission_id,
            "mission_name": mission_name,
            "roles_executed": len(handoffs),
            "total_time_seconds": total_time,
            "handoffs": {r: asdict(h) for r, h in handoffs.items()},
        }

    def cleanup_sandboxes(self) -> None:
        """Remove temporary branch worktree directories."""
        for path in self.sandboxes:
            if os.path.exists(path):
                try:
                    shutil.rmtree(path, ignore_errors=True)
                except Exception:
                    pass
        self.sandboxes.clear()
