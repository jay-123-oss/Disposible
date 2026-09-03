"""TeamStoreManager agent managing agent grouping, team boundaries, permissions, and team metadata."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Set

from agents.commstate.exceptions import TeamStoreError
from core.agent_base import BaseAgent


logger = logging.getLogger("FractalCore.CommState.TeamStoreManager")


# ==============================================================================
# L5 Atomic Team Store Subagents
# ==============================================================================

class TeamCreator(BaseAgent):
    """L5 agent instantiating new team definitions with permissions and member rosters."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TeamCreator %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        team_name = payload.get("team_name", "unnamed_team")
        members = list(payload.get("members", []))
        permissions = list(payload.get("permissions", ["read", "write"]))

        team_record = {
            "team_name": team_name,
            "members": members,
            "permissions": permissions,
            "created_at": time.time(),
            "updated_at": time.time(),
        }
        return {"status": "COMPLETED", "team_record": team_record}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if "team_record" not in result:
            raise TeamStoreError("TeamCreator produced invalid team record.")
        return result

    def cleanup(self) -> None:
        logger.debug("TeamCreator %s cleaned up.", self.agent_id)


class TeamUpdater(BaseAgent):
    """L5 agent adding or removing members from active teams."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TeamUpdater %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        team_record = dict(payload.get("team_record", {}))
        add_members = payload.get("add_members", [])
        remove_members = payload.get("remove_members", [])

        current = set(team_record.get("members", []))
        current.update(add_members)
        current.difference_update(remove_members)

        team_record["members"] = list(current)
        team_record["updated_at"] = time.time()
        return {"status": "COMPLETED", "team_record": team_record}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TeamUpdater %s cleaned up.", self.agent_id)


class TeamFinder(BaseAgent):
    """L5 agent querying teams by name or locating all teams an agent belongs to."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TeamFinder %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        team_store = payload.get("team_store", {})
        agent_id = payload.get("agent_id")
        team_name = payload.get("team_name")

        if team_name:
            team = team_store.get(team_name)
            return {"status": "COMPLETED", "matched_teams": [team] if team else []}

        if agent_id:
            matched = [t for t in team_store.values() if agent_id in t.get("members", [])]
            return {"status": "COMPLETED", "matched_teams": matched}

        return {"status": "COMPLETED", "matched_teams": list(team_store.values())}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TeamFinder %s cleaned up.", self.agent_id)


class TeamDeleter(BaseAgent):
    """L5 agent disbanding and deleting team groupings."""

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TeamDeleter %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        team_name = payload.get("team_name")
        team_store = dict(payload.get("team_store", {}))

        deleted = False
        if team_name and team_name in team_store:
            del team_store[team_name]
            deleted = True

        return {"status": "COMPLETED", "team_store": team_store, "deleted": deleted}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TeamDeleter %s cleaned up.", self.agent_id)


# ==============================================================================
# L4 TeamStoreManager Agent
# ==============================================================================

class TeamStoreManager(BaseAgent):
    """L4 coordinator managing agent clusters, team rosters, and access boundaries."""

    def __init__(
        self,
        name: str = "TeamStoreManager",
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 128,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
        auto_spawn_subagents: bool = True,
    ) -> None:
        default_caps = capabilities or [
            "team_store_management",
            "team_creation",
            "team_roster_updates",
            "team_queries",
        ]
        super().__init__(
            name=name,
            capabilities=default_caps,
            model=model,
            resources_mb=resources_mb,
            parent=parent,
            max_depth=max_depth,
            llm_endpoint=llm_endpoint,
            agent_id=agent_id or "C3_TEAM_STORE_MANAGER",
        )

        self._teams: Dict[str, Dict[str, Any]] = {}
        self.creator: Optional[TeamCreator] = None
        self.updater: Optional[TeamUpdater] = None
        self.finder: Optional[TeamFinder] = None
        self.deleter: Optional[TeamDeleter] = None

        if auto_spawn_subagents and self.depth < self.max_depth:
            self._spawn_subagents()

        self.register_tool("create_team", self.create_team)
        self.register_tool("add_to_team", self.add_to_team)
        self.register_tool("find_teams", self.find_teams)
        self.register_tool("delete_team", self.delete_team)

    def _spawn_subagents(self) -> None:
        """Spawn atomic team store subagents (Rule 1 & Rule 5)."""
        logger.info("TeamStoreManager %s spawning subagents...", self.agent_id)
        child_depth = self.depth + 2
        self.creator = self.spawn_subagent(
            TeamCreator,
            name="TeamCreator",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.updater = self.spawn_subagent(
            TeamUpdater,
            name="TeamUpdater",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.finder = self.spawn_subagent(
            TeamFinder,
            name="TeamFinder",
            max_depth=child_depth,
            resources_mb=64,
        )
        self.deleter = self.spawn_subagent(
            TeamDeleter,
            name="TeamDeleter",
            max_depth=child_depth,
            resources_mb=64,
        )

    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        logger.debug("TeamStoreManager %s initialized.", self.agent_id)

    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        payload = task_envelope.get("payload", {})
        team_name = payload.get("team_name", "default_team")
        members = payload.get("members", [])
        rec = self.create_team(team_name=team_name, members=members)
        return {"status": "COMPLETED", "team": rec}

    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result

    def cleanup(self) -> None:
        logger.debug("TeamStoreManager %s cleanup complete.", self.agent_id)

    def create_team(self, team_name: str, members: Optional[List[str]] = None, permissions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create new team record."""
        p_env = {"payload": {"team_name": team_name, "members": members or [], "permissions": permissions or []}}
        res = self.creator.process(p_env) if self.creator else {"team_record": {"team_name": team_name, "members": members or []}}
        record = res["team_record"]
        self._teams[team_name] = record
        return record

    def add_to_team(self, team_name: str, member_ids: List[str]) -> Optional[Dict[str, Any]]:
        """Add agents to team roster."""
        if team_name not in self._teams:
            return None
        p_env = {"payload": {"team_record": self._teams[team_name], "add_members": member_ids}}
        res = self.updater.process(p_env) if self.updater else {"team_record": self._teams[team_name]}
        self._teams[team_name] = res["team_record"]
        return self._teams[team_name]

    def find_teams(self, agent_id: Optional[str] = None, team_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find teams by name or agent membership."""
        p_env = {"payload": {"team_store": self._teams, "agent_id": agent_id, "team_name": team_name}}
        res = self.finder.process(p_env) if self.finder else {"matched_teams": list(self._teams.values())}
        return res.get("matched_teams", [])

    def delete_team(self, team_name: str) -> bool:
        """Disband team."""
        p_env = {"payload": {"team_store": self._teams, "team_name": team_name}}
        res = self.deleter.process(p_env) if self.deleter else {"deleted": False}
        if res.get("deleted"):
            self._teams.pop(team_name, None)
            return True
        return False
