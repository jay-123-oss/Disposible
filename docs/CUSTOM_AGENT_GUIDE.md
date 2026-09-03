# How to Build Custom Agents

1. Subclass `BaseAgent` from `core.agent_base`.
2. Set `max_depth=2` to respect two-tier supervisory bounding.
3. Register domain tools using `self.register_tool()`.
4. Add custom capability strings to `self.capabilities`.
5. Register into `AgentRegistry`.
