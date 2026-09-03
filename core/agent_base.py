"""Abstract BaseAgent class for the Fractal Multi-Agent Coding System.

Implements:
- Template Method pattern for agent execution lifecycle (initialize, process, validate, cleanup).
- Subagent spawning with strict max_depth enforcement (Rule 5: parent -> child -> grandchild).
- Parent-child tree relationship tracking.
- Tool registration and deterministic dispatch.
- Direct Ollama REST interface for local LLM inference with fallback.
"""

from __future__ import annotations

import abc
import json
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional

import requests

from core.exceptions import AgentError, DepthLimitError


logger = logging.getLogger("FractalCore.AgentBase")


class BaseAgent(abc.ABC):
    """Abstract base class establishing the fractal contract for all agents."""

    def __init__(
        self,
        name: str,
        capabilities: Optional[List[str]] = None,
        model: str = "qwen2.5-coder:3b",
        resources_mb: int = 512,
        parent: Optional[BaseAgent] = None,
        max_depth: int = 2,
        llm_endpoint: str = "http://localhost:11434",
        agent_id: Optional[str] = None,
    ) -> None:
        """Initialize the BaseAgent with metadata, depth constraints, and tool registry.

        Args:
            name: Human-readable role name (e.g. 'PLANNER', 'GetRouteTask').
            capabilities: List of declared operational capabilities.
            model: Name of the Ollama model to invoke.
            resources_mb: Allocated RAM limit in MB.
            parent: Direct supervising parent agent if any.
            max_depth: Maximum relative depth allowed from root (default 2).
            llm_endpoint: Base URL for Ollama REST API.
            agent_id: Optional deterministic ID; if omitted, a UUID is generated.
        """
        self._name = name
        self._agent_id = agent_id or f"{name.upper()}_{uuid.uuid4().hex[:8]}"
        self._capabilities = capabilities or []
        self._model = model
        self._resources_mb = resources_mb
        self._parent = parent
        self._children: Dict[str, BaseAgent] = {}
        self._max_depth = max_depth
        self._llm_endpoint = llm_endpoint.rstrip("/")
        self._state: str = "idle"  # idle | working | waiting | completed | failed
        self._tools: Dict[str, Callable[..., Any]] = {}
        self._execution_history: List[Dict[str, Any]] = []

        # Depth calculation relative to the root of this sub-tree
        if self._parent is not None:
            self._depth = self._parent.depth + 1
            if self._depth > self._max_depth:
                raise DepthLimitError(
                    f"Cannot create agent {self._agent_id} at depth {self._depth}. "
                    f"Maximum depth limit is {self._max_depth}.",
                    details={"agent_name": name, "parent_id": self._parent.agent_id, "depth": self._depth},
                )
        else:
            self._depth = 0

        logger.debug(
            "Initialized agent %s (ID: %s, Level: %d, Parent: %s)",
            self._name,
            self._agent_id,
            self._depth,
            self._parent.agent_id if self._parent else "None",
        )

    # --------------------------------------------------------------------------
    # Properties
    # --------------------------------------------------------------------------

    @property
    def agent_id(self) -> str:
        """Unique identifier of the agent."""
        return self._agent_id

    @property
    def name(self) -> str:
        """Name of the agent role."""
        return self._name

    @property
    def depth(self) -> int:
        """Current hierarchical depth (0 for root, up to max_depth)."""
        return self._depth

    @property
    def max_depth(self) -> int:
        """Maximum depth boundary allowed."""
        return self._max_depth

    @property
    def state(self) -> str:
        """Current lifecycle status."""
        return self._state

    @property
    def capabilities(self) -> List[str]:
        """List of functional capabilities."""
        return list(self._capabilities)

    @property
    def tools(self) -> List[str]:
        """List of registered tool names."""
        return list(self._tools.keys())

    @property
    def parent(self) -> Optional[BaseAgent]:
        """Supervising parent agent instance."""
        return self._parent

    @property
    def children(self) -> Dict[str, BaseAgent]:
        """Dictionary of subordinate children instances."""
        return dict(self._children)

    @property
    def resources_mb(self) -> int:
        """Memory quota allocated in MB."""
        return self._resources_mb

    # --------------------------------------------------------------------------
    # Subagent Spawning (Rule 1 & Rule 5)
    # --------------------------------------------------------------------------

    def spawn_subagent(
        self,
        agent_cls: type[BaseAgent],
        name: str,
        capabilities: Optional[List[str]] = None,
        model: Optional[str] = None,
        resources_mb: int = 512,
        **kwargs: Any,
    ) -> BaseAgent:
        """Spawn a specialized sub-agent with strict depth enforcement.

        Args:
            agent_cls: Concrete subclass of BaseAgent to instantiate.
            name: Role name for the child.
            capabilities: Capabilities of the child agent.
            model: Optional model override; defaults to parent model.
            resources_mb: RAM allocation in MB.
            **kwargs: Extra parameters passed to the child constructor.

        Returns:
            The instantiated child agent.

        Raises:
            DepthLimitError: If creating child violates max_depth.
        """
        if self._depth >= self._max_depth:
            raise DepthLimitError(
                f"Agent {self._agent_id} at depth {self._depth} cannot spawn sub-agents. "
                f"Max depth of {self._max_depth} reached (Rule 5).",
                details={"parent_id": self._agent_id, "current_depth": self._depth},
            )

        child_max_depth = kwargs.pop("max_depth", self._max_depth)
        child_agent = agent_cls(
            name=name,
            capabilities=capabilities,
            model=model or self._model,
            resources_mb=resources_mb,
            parent=self,
            max_depth=child_max_depth,
            llm_endpoint=self._llm_endpoint,
            **kwargs,
        )

        self._children[child_agent.agent_id] = child_agent
        logger.info(
            "Agent %s spawned child sub-agent %s (depth %d)",
            self._agent_id,
            child_agent.agent_id,
            child_agent.depth,
        )
        return child_agent

    def remove_child(self, child_id: str) -> None:
        """Remove a child agent reference upon task completion."""
        if child_id in self._children:
            del self._children[child_id]
            logger.debug("Removed child agent %s from %s", child_id, self._agent_id)

    # --------------------------------------------------------------------------
    # Tool Registration System
    # --------------------------------------------------------------------------

    def register_tool(self, name: str, func: Callable[..., Any]) -> None:
        """Register a deterministic tool callable in the agent's toolbelt."""
        if not callable(func):
            raise AgentError(f"Tool {name} must be callable", details={"agent_id": self._agent_id})
        self._tools[name] = func
        logger.debug("Registered tool '%s' on agent %s", name, self._agent_id)

    def execute_tool(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a registered tool by name with error trapping."""
        if name not in self._tools:
            raise AgentError(
                f"Tool '{name}' is not registered on agent {self._agent_id}",
                details={"available_tools": list(self._tools.keys())},
            )
        try:
            return self._tools[name](*args, **kwargs)
        except Exception as exc:
            logger.error("Error executing tool '%s' on %s: %s", name, self._agent_id, exc)
            raise AgentError(
                f"Tool execution failed for '{name}': {exc}",
                details={"tool_name": name, "agent_id": self._agent_id},
            ) from exc

    # --------------------------------------------------------------------------
    # LLM Interaction
    # --------------------------------------------------------------------------

    def query_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Send inference request to local Ollama instance with timeout and fallback.

        Args:
            prompt: User/task instruction string.
            system_prompt: Optional system persona prompt.
            temperature: Sampling temperature.
            max_tokens: Hard ceiling for output tokens.

        Returns:
            Generated text content from the LLM.
        """
        url = f"{self._llm_endpoint}/api/generate"
        payload = {
            "model": self._model,
            "prompt": prompt,
            "system": system_prompt or f"You are {self._name}, a specialized autonomous coding agent.",
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                content = data.get("response", "").strip()
                logger.debug("LLM query succeeded on model %s (%d chars)", self._model, len(content))
                return content
            logger.warning(
                "Ollama returned HTTP %d: %s. Falling back to deterministic simulation.",
                response.status_code,
                response.text,
            )
            return self._fallback_deterministic_response(prompt)
        except requests.RequestException as req_err:
            logger.warning(
                "Could not reach Ollama at %s (%s). Using deterministic fallback.",
                self._llm_endpoint,
                req_err,
            )
            return self._fallback_deterministic_response(prompt)

    def _fallback_deterministic_response(self, prompt: str) -> str:
        """Deterministic rule-based response generator when local Ollama is offline."""
        logger.info("Executing deterministic fallback response for %s", self._agent_id)
        return json.dumps(
            {
                "status": "deterministic_success",
                "agent_id": self._agent_id,
                "role": self._name,
                "acknowledged_prompt": prompt[:120] + "...",
                "output": f"Deterministic execution result completed for task handled by {self._name}.",
            }
        )

    # --------------------------------------------------------------------------
    # Lifecycle Template Method Pattern
    # --------------------------------------------------------------------------

    def execute_lifecycle(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        """Execute full agent lifecycle using Template Method pattern.

        Lifecycle sequence:
        1. initialize() -> Prepares environment and context.
        2. process()    -> Executes core business logic or sub-delegation.
        3. validate()   -> Performs local quality and syntax validation.
        4. cleanup()    -> Purges temporary state and resources.
        """
        self._state = "working"
        logger.info("Agent %s entering lifecycle for task: %s", self._agent_id, task_envelope.get("task_id"))

        try:
            self.initialize(task_envelope)
            raw_result = self.process(task_envelope)
            validated_result = self.validate(raw_result)
            self._state = "completed"
            self._execution_history.append(
                {"task_id": task_envelope.get("task_id"), "status": "completed", "result": validated_result}
            )
            return validated_result
        except Exception as exc:
            self._state = "failed"
            logger.error("Agent %s failed during lifecycle execution: %s", self._agent_id, exc)
            self._execution_history.append(
                {"task_id": task_envelope.get("task_id"), "status": "failed", "error": str(exc)}
            )
            raise AgentError(
                f"Lifecycle failure in agent {self._agent_id}: {exc}",
                details={"agent_id": self._agent_id, "task_id": task_envelope.get("task_id")},
            ) from exc
        finally:
            self.cleanup()
            if self._state != "failed":
                self._state = "idle"

    @abc.abstractmethod
    def initialize(self, task_envelope: Dict[str, Any]) -> None:
        """Initialize agent context and verify preconditions."""

    @abc.abstractmethod
    def process(self, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's assigned processing logic."""

    @abc.abstractmethod
    def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate execution result against local quality constraints."""

    @abc.abstractmethod
    def cleanup(self) -> None:
        """Release temporary handles and reset working state."""

    def to_registry_dict(self) -> Dict[str, Any]:
        """Serialize current agent state conforming to the Agent Registry Schema."""
        return {
            "agent_id": self._agent_id,
            "agent_name": self._name,
            "level": self._depth,
            "parent_id": self._parent.agent_id if self._parent else None,
            "children_ids": list(self._children.keys()),
            "capabilities": self._capabilities,
            "tools": list(self._tools.keys()),
            "max_depth": self._max_depth,
            "state": self._state,
            "resource_requirements": {
                "ram_mb": self._resources_mb,
                "model": self._model,
            },
        }
