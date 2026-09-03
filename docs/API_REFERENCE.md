# API Reference Manual

## 1. Orchestrator API
### `submit_task(intent, assigned_capability=None, priority=TaskPriority.NORMAL, context=None) -> str`
Enqueues a new asynchronous coding task into the priority queue.
- **Parameters**:
  - `intent` (*str*): Natural language instruction.
  - `assigned_capability` (*str*, optional): Explicit domain routing key.
  - `priority` (*TaskPriority*): Priority enum (`CRITICAL`, `HIGH`, `NORMAL`, `LOW`).
  - `context` (*dict*, optional): Additional execution metadata.
- **Returns**: `task_id` (*str*).

### `wait_for_completion(timeout=60.0) -> bool`
Blocks synchronously until all queued tasks are resolved or timeout occurs.

### `get_system_status() -> dict`
Returns live metrics on active workers, queued tasks, agent count, and memory consumption.

## 2. Agent Registry API
### `register_agent(agent: BaseAgent) -> None`
Enrolls an agent instance into the central directory. Enforces RAM limits and unique IDs.

### `get_agent(agent_id: str) -> Optional[BaseAgent]`
Retrieves registered agent by unique identifier.

### `find_by_capability(capability: str) -> List[BaseAgent]`
Discovers all agents exporting the requested capability tag.
