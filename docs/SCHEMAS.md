# Schemas and Data Transfer Objects

## 1. TaskEnvelope
```json
{
  "task_id": "TSK_a1b2c3d4",
  "intent": "Implement JWT verification middleware",
  "capability": "coding",
  "priority": "HIGH",
  "status": "COMPLETED",
  "assigned_agent_id": "C4_MIDDLEWARE_AGENT",
  "payload": {},
  "created_at": 1725321000.0,
  "completed_at": 1725321004.2
}
```

## 2. AgentMetadata
```json
{
  "agent_id": "TV1_TEST_ORCHESTRATOR",
  "name": "TestOrchestrator",
  "level": "L3",
  "depth": 0,
  "max_depth": 2,
  "resources_mb": 256,
  "capabilities": ["test_orchestration", "system_testing"],
  "children_count": 13
}
```
