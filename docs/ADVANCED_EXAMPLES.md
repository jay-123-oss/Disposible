# Advanced Examples

### Example 2: Spawning Subagents
```python
from core.agent_base import BaseAgent

class ParentCoordinator(BaseAgent):
    def process(self, envelope):
        worker = self.spawn_subagent(BaseAgent, name="WorkerSubAgent")
        return worker.process(envelope)
```
