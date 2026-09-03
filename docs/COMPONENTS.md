# System Components Catalog

## 1. Core Framework Components
- **`BaseAgent`**: Abstract foundation defining lifecycle hooks (`initialize`, `process`, `validate`, `cleanup`), tool registration, and hierarchical subagent spawning.
- **`Orchestrator`**: Master coordinator maintaining worker pools, task scheduling, capability routing, and graceful shutdowns.
- **`AgentRegistry`**: Singleton directory tracking agent metadata, capabilities, hierarchy trees, and RAM quotas.
- **`TaskQueue`**: Thread-safe priority queue sorting by `CRITICAL`, `HIGH`, `NORMAL`, and `LOW`.
- **`StateManager`**: Checkpoint engine creating isolated snapshot directories, rollbacks, and JSON persistence.
- **`Communication`**: Mailbox queue and stigmergic trace blackboard supporting decay and pheromone trails.
- **`QualityGate`**: Pipeline checkpoints (QG_1 through QG_5) assessing syntax, types, coverage, security, and complexity.
- **`Monitor`**: Real-time heartbeat, error rate tracker, CPU/RAM telemetry, and anomaly detector.
- **`Sandbox`**: Process-isolated execution barrier enforcing memory caps, CPU timeouts, and dangerous syscall blocking.

## 2. Layer Coordinators (L3)
- **`IntentClarifier` (P1)**: Planning root validating user objectives.
- **`DeveloperAgent` (C1)**: Coding root orchestrating backend, frontend, and database subagents.
- **`TestOrchestrator` (T1/TV1)**: Testing root conducting unit, integration, system, and performance benchmarks.
- **`SecurityOrchestrator` (S1)**: Security root executing AST and static vulnerability audits.
- **`QualityOrchestrator` (Q1)**: Quality root checking cyclomatic complexity and PEP 8 compliance.
- **`InfrastructureOrchestrator` (I1)**: DevOps root producing Docker, Compose, and K8s manifests.
- **`CommStateOrchestrator` (CS1)**: State synchronization and replay engine root.
- **`MonitoringOrchestrator` (M1)**: Telemetry, observability, and anomaly alert root.
- **`IntegrationOrchestrator` (IA1)**: System bootstrap, workflow execution, and dependency injection root.
- **`DocumentationOrchestrator` (D1)**: Documentation suite compiler.
