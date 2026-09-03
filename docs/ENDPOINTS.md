# Endpoints Catalog

| HTTP Method | Path | Description | Required Role / Auth |
|---|---|---|---|
| `POST` | `/api/v1/tasks` | Submits a task for autonomous execution | Bearer Token |
| `GET` | `/api/v1/tasks/{id}` | Retrieves execution result and lifecycle trace | Bearer Token |
| `GET` | `/api/v1/tasks` | Lists all pending, active, and completed tasks | Admin |
| `DELETE` | `/api/v1/tasks/{id}` | Cancels queued or running task | Admin |
| `GET` | `/api/v1/agents` | Lists registered agents and capability mappings | Bearer Token |
| `GET` | `/api/v1/agents/{id}` | Detailed telemetry and subagent tree for agent | Bearer Token |
| `GET` | `/api/v1/health` | Comprehensive cluster health status | Public |
| `GET` | `/api/v1/metrics` | Prometheus telemetry metric stream | Admin |
