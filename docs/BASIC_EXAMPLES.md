# Basic Examples

### Example 1: Submit Single Task
```python
from core.orchestrator import Orchestrator

orch = Orchestrator()
orch.start()

task_id = orch.submit_task("Calculate Fibonacci numbers", capability="coding")
orch.wait_for_completion()
orch.stop()
```
