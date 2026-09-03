# Extension & Custom Agent Guide

## Writing a Custom Agent
```python
from core.agent_base import BaseAgent

class CustomAnalyzer(BaseAgent):
    def initialize(self, task_envelope):
        pass

    def process(self, task_envelope):
        payload = task_envelope.get("payload", {})
        return {"status": "COMPLETED", "result": "Analyzed successfully"}

    def validate(self, result):
        return result

    def cleanup(self):
        pass
```

## Registering in Registry
```python
from core.registry import AgentRegistry

registry = AgentRegistry()
agent = CustomAnalyzer(name="CustomAnalyzer", capabilities=["custom_analysis"])
registry.register_agent(agent)
```
