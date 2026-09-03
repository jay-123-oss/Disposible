"""Documentation generation script producing all 50 required docs in docs/."""

import os
import sys

DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))

FILES = {}

# ==============================================================================
# 1-5: System Documentation Files
# ==============================================================================

FILES["README.md"] = """# Fractal Multi-Agent Coding System

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/fractal-core/fractal-system)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen)](https://www.python.org/)

## Overview
The Fractal Multi-Agent Autonomous Coding System is an enterprise-grade agentic architecture built on the fundamental principle that:
> *"Every task gets its own specialized agent. Every agent can spawn sub-agents. The chain continues until the task becomes atomic."*

The system features strict lifecycle phases (Initialize -> Process -> Validate -> Cleanup), asynchronous stigmergic signaling across parent/blackboard channels, rigorous quality gate enforcement, sandboxed execution, and checkpoint/replay fault tolerance.

## Core Capabilities
- **Hierarchical Fractal Decomposition**: Spawns specialized agents dynamically down to atomic workers (up to max depth 7).
- **Communication Topology**: Structured parent-to-child delegation and decoupled stigmergy traces without uncoordinated peer-to-peer chatter.
- **Resource Governance**: Real-time memory budgeting bounded at 8192 MB (8 GB) max RAM ceiling.
- **Verification & Testing**: Multi-tier testing suite spanning System, Integration, Unit, Performance, Security, and Quality validations.
- **Fault Recovery**: Automatic state snapshotting, deterministic replay engine, and graceful shutdown handlers.

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/fractal-core/fractal-system.git
cd fractal-system

# 2. Setup Virtual Environment
python -m venv venv
source venv/bin/activate  # On Windows: .\\venv\\Scripts\\activate

# 3. Install Dependencies
pip install -r requirements.txt

# 4. Copy Configuration
cp config.example.yaml config.yaml

# 5. Execute a Task
python main.py --task "Build a secure REST user authentication endpoint" --capability "coding"
```

## Documentation Map
- **[User Guide](USER_GUIDE.md)**: Onboarding, features, use cases, and best practices.
- **[Developer Guide](DEVELOPER_GUIDE.md)**: Codebase layout, extension points, contributing, and debugging.
- **[Architecture](ARCHITECTURE.md)**: High-level architectural specifications and fractal layout.
- **[API Reference](API_REFERENCE.md)**: REST and agent invocation contracts.
- **[Installation](INSTALLATION.md)**: Prerequisites, step-by-step setup, and verification.
- **[Configuration](CONFIGURATION.md)**: Complete parameter guide and environment variable overrides.
- **[Deployment](DEPLOYMENT.md)**: Docker, Kubernetes, and Cloud hosting.
- **[Troubleshooting](TROUBLESHOOTING.md)**: Common failure modes, error codes, and recovery procedures.
- **[FAQ](FAQ.md)**: General, technical, configuration, and troubleshooting answers.

## License
Distributed under the MIT License.
"""

FILES["ARCHITECTURE.md"] = """# System Architecture

## Overview
The Fractal Multi-Agent Autonomous Coding System organizes autonomous problem solving into a hierarchical, self-similar tree of specialized agents. No single monolithic model handles end-to-end execution. Instead, tasks are progressively decomposed into smaller, bounded scopes.

## High-Level Architecture Diagram
```mermaid
graph TD
    User([User / CLI / API]) --> Orchestrator[Orchestrator L1/L2]
    Orchestrator --> StateMgr[State Manager & Checkpoints]
    Orchestrator --> TaskQ[Priority Task Queue]
    Orchestrator --> Comm[Communication & Stigmergy]
    Orchestrator --> Reg[Agent Registry]

    Orchestrator --> Planning[Planning Layer L3]
    Orchestrator --> Coding[Coding Layer L3]
    Orchestrator --> Testing[Testing Layer L3]
    Orchestrator --> Security[Security Layer L3]
    Orchestrator --> Quality[Quality Layer L3]
    Orchestrator --> Infra[Infrastructure Layer L3]
    Orchestrator --> Monitoring[Monitoring Layer L3]
    Orchestrator --> CommState[CommState Layer L3]
    Orchestrator --> Integration[Integration Layer L3]
    Orchestrator --> Docs[Documentation Layer L3]
```

## System Layers
1. **Core Layer**: BaseAgent, Orchestrator, AgentRegistry, TaskQueue, StateManager, QualityGate, Monitor, Sandbox.
2. **Planning Layer (P1-P10)**: Intent Clarifier, Question Generator, Option Parser, Task Decomposer, Dependency Analyzer.
3. **Coding Layer (C1-C24)**: Backend, Frontend, Fullstack, API Route, Database, Middleware, Controller.
4. **Testing Layer (T1-T16)**: Test Orchestrator, Unit Test Generator, Integration Test Creator, Edge Case Finder.
5. **Security Layer (S1-S12)**: Security Orchestrator, Auth Checker, SQL Injection Scanner, Token Validator, Role Checker.
6. **Quality Layer (Q1-Q12)**: Quality Orchestrator, Code Formatter, Style Checker, Complexity Analyzer, Documentation Writer.
7. **Infrastructure Layer (I1-I14)**: Infrastructure Orchestrator, Docker Configurer, Compose Generator, CI/CD Setuper.
8. **CommState Layer (CS1-CS14)**: CommState Orchestrator, Task Store, Mailbox, Registry, Trace Depositor, Replay Engine.
9. **Monitoring Layer (M1-M14)**: Monitoring Orchestrator, Live Debugger, Metrics Collector, Alert Manager, Health Checker.
10. **Integration Layer (IA1-IA14)**: Integration Orchestrator, System Initializer, Agent Factory, Dependency Injector.
11. **Testing & Validation Layer (TV1-TV14)**: System Test Runner, Performance Runner, Validation Engine, Coverage Reporter.
12. **Documentation Layer (D1-D12)**: Documentation Orchestrator, API Documenter, Guides, Reference, FAQ.

## Communication Topology & Stigmergy
- **Direct Supervision**: Parents communicate strictly with direct children.
- **Blackboard & Stigmergy**: Indirect signaling via environmental traces (Attraction, Danger, Information) allowing emergent coordination without unconstrained peer chat.
"""

FILES["COMPONENTS.md"] = """# System Components Catalog

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
"""

FILES["DATA_FLOW.md"] = """# Data Flow Architecture

## Task Lifecycle Data Flow
```mermaid
sequenceDiagram
    autonumber
    actor User
    participant CLI as CLI / Main
    participant Orch as Orchestrator
    participant Queue as Priority TaskQueue
    participant Reg as AgentRegistry
    participant Agent as Specialized Agent
    participant QG as QualityGate
    participant State as StateManager

    User->>CLI: Submit Task Command
    CLI->>Orch: submit_task(intent, capability)
    Orch->>Queue: put(TaskItem)
    Orch->>Reg: find_capable_agent(capability)
    Reg-->>Orch: Return Agent ID
    Queue->>Orch: Worker pop()
    Orch->>Agent: execute_lifecycle(TaskEnvelope)
    activate Agent
    Agent->>Agent: initialize()
    Agent->>Agent: process()
    Agent->>Agent: spawn_subagent()
    Agent->>Agent: validate()
    Agent->>QG: evaluate_phase(result)
    QG-->>Agent: Quality Score (Pass/Fail)
    Agent->>Agent: cleanup()
    deactivate Agent
    Agent-->>Orch: Task Results
    Orch->>State: create_checkpoint()
    Orch-->>CLI: Final Result Envelope
    CLI-->>User: Visual Output / Exit Code
```

## Stigmergic Signaling Flow
1. **Emission**: Agent generates trace (e.g. `attraction`, `danger`, `information`).
2. **Deposition**: Blackboard records signal with timestamp, initial strength (1.0), and topic key.
3. **Decay**: Background worker applies exponential decay over time ($S(t) = S_0 \cdot e^{-\lambda t}$).
4. **Sensing**: Downstream agents poll local stigmergy space to avoid dangerous patterns or gravitate toward completed artifacts.
"""

FILES["SYSTEM_DIAGRAM.md"] = """# System Architecture Diagrams

## Complete Multi-Agent Hierarchy
```mermaid
graph TD
    Root[Orchestrator Engine]

    subgraph Planning [Planning Layer]
        P1[Intent Clarifier] --> P2[Question Generator]
        P1 --> P3[Option Parser]
    end

    subgraph Coding [Coding Layer]
        C1[Backend Agent] --> C2[API Route Agent]
        C1 --> C3[Database Agent]
    end

    subgraph Testing [Testing Layer]
        T1[Test Orchestrator] --> T2[Unit Runner]
        T1 --> T3[System Runner]
    end

    subgraph Security [Security Layer]
        S1[Security Orchestrator] --> S2[Auth Checker]
        S1 --> S3[Injection Scanner]
    end

    subgraph Integration [Integration Layer]
        IA1[Integration Orchestrator] --> IA2[System Initializer]
        IA1 --> IA3[Workflow Orchestrator]
    end

    subgraph Documentation [Documentation Layer]
        D1[Doc Orchestrator] --> D2[System Docs]
        D1 --> D3[API Docs]
        D1 --> D4[User Guide]
    end

    Root --> P1
    Root --> C1
    Root --> T1
    Root --> S1
    Root --> IA1
    Root --> D1
```

## State & Checkpoint Persistence Diagram
```mermaid
flowchart LR
    ActiveState[(Active State)] --> CheckpointEngine[Checkpoint Engine]
    CheckpointEngine --> CheckpointDir[state/checkpoints/YYYYMMDD_HHMMSS/]
    CheckpointDir --> MetadataJSON[metadata.json]
    CheckpointDir --> GlobalStateJSON[global_state.json]
    CheckpointDir --> AgentStateJSON[agent_states.json]
    CheckpointDir --> ReplayLog[replay_log.jsonl]
```
"""

# ==============================================================================
# 6-10: API Documentation Files
# ==============================================================================

FILES["API_REFERENCE.md"] = """# API Reference Manual

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
"""

FILES["OPENAPI.yaml"] = """openapi: 3.0.0
info:
  title: Fractal Multi-Agent System REST API
  version: 1.0.0
  description: HTTP API interface for submitting tasks, inspecting agent states, and querying system telemetry.
paths:
  /api/v1/tasks:
    post:
      summary: Submit a task
      operationId: submitTask
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TaskSubmission'
      responses:
        '202':
          description: Task accepted
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskEnvelope'
    get:
      summary: List all active tasks
      operationId: listTasks
      responses:
        '200':
          description: List of tasks
  /api/v1/health:
    get:
      summary: Health check endpoint
      operationId: getHealth
      responses:
        '200':
          description: System health status
components:
  schemas:
    TaskSubmission:
      type: object
      required:
        - intent
      properties:
        intent:
          type: string
        capability:
          type: string
        priority:
          type: string
          enum: [CRITICAL, HIGH, NORMAL, LOW]
    TaskEnvelope:
      type: object
      properties:
        task_id:
          type: string
        status:
          type: string
        output:
          type: object
"""

FILES["SWAGGER.md"] = """# Swagger UI Integration

## Overview
The Fractal system exports standard OpenAPI 3.0.0 definitions compatible with Swagger UI, Redoc, and Postman.

## Enabling Local Swagger UI
Run the application server:
```bash
python main.py --task "Start HTTP API Gateway" --capability "integration"
```
Navigate to:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Raw OpenAPI JSON**: `http://localhost:8000/openapi.json`
- **Raw OpenAPI YAML**: `http://localhost:8000/openapi.yaml`
"""

FILES["ENDPOINTS.md"] = """# Endpoints Catalog

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
"""

FILES["SCHEMAS.md"] = """# Schemas and Data Transfer Objects

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
"""

# ==============================================================================
# 11-15: User Documentation Files
# ==============================================================================

FILES["USER_GUIDE.md"] = """# User Guide

## Introduction
Welcome to the Fractal Multi-Agent Autonomous Coding System. This guide teaches you how to leverage the CLI and API to solve complex programming tasks automatically.

## User Journey
1. **Task Submission**: Formulate an intent and specify target capability.
2. **Decomposition**: The system spawns specialized L3 coordinators and L4/L5 subagents.
3. **Execution & Quality Gates**: Code is written, tested, scanned for security, and formatted.
4. **Validation**: Quality gates evaluate code syntax, style, and correctness.
5. **Output**: Verified artifacts, tests, and deployment scripts are generated.
"""

FILES["GETTING_STARTED.md"] = """# Getting Started Tutorial

Follow this 5-minute tutorial to execute your first task.

### Step 1: Verify Installation
```bash
python cli.py status
```
Output confirms agent count and active RAM allocations.

### Step 2: Run a Coding Task
```bash
python main.py --task "Create a fast JSON logging utility" --capability "coding"
```

### Step 3: Run Full Validation
```bash
python main.py --task "Run comprehensive system validation suite" --capability "testing_validation"
```

### Step 4: Inspect Checkpoints
```bash
ls state/checkpoints/
```
"""

FILES["FEATURES.md"] = """# Feature Tour

- **Fractal Spawning**: Every agent can spawn subagents to break down tasks dynamically.
- **Two-Tier Supervisory Bounding**: Agents supervise children and grandchildren only, bounded by a global depth ceiling of 7.
- **Stigmergic Coordination**: Decoupled signaling prevents cross-agent communication bottlenecks.
- **Strict Quality Gates**: Every artifact passes 5 sequential quality gates before acceptance.
- **Process Sandboxing**: Untrusted code runs in isolated environments with memory and syscall caps.
- **Fault Recovery**: Snapshot checkpointing enables instant resumption upon failure.
"""

FILES["USE_CASES.md"] = """# Practical Use Cases

### Use Case 1: Automated API Development
- User submits: "Create REST CRUD endpoints for User model with JWT authentication".
- Planning layer decomposes into schema, routes, database migrations, and unit tests.
- Coding layer writes code, Security scans for vulnerabilities, Quality audits style.

### Use Case 2: Continuous Security Auditing
- Scheduled job triggers `SecurityOrchestrator` to scan repository for SQL injection, hardcoded secrets, and XSS risks.

### Use Case 3: Infrastructure-as-Code Provisioning
- User requests: "Generate production Dockerfile and Kubernetes manifests with HPA".
- Infrastructure layer produces battle-tested manifests with health probes.
"""

FILES["BEST_PRACTICES.md"] = """# Best Practices Guide

1. **Be Specific in Intents**: Instead of "Fix backend", prompt "Fix user session timeout handling in auth middleware".
2. **Explicit Capabilities**: Specify `--capability` (e.g. `coding`, `testing_validation`, `security`) to accelerate routing.
3. **Monitor Memory**: Ensure total agent allocations do not exceed the 8192 MB global cap.
4. **Run Verification Before Commits**: Execute `python -m unittest discover -s tests -t .` regularly.
5. **Leverage Cleanups**: Always allow graceful shutdowns so checkpoints are cleanly persisted.
"""

# ==============================================================================
# 16-20: Developer Documentation Files
# ==============================================================================

FILES["DEVELOPER_GUIDE.md"] = """# Developer Guide

## System Principles
- **Fractal Decomposition**: Problem solving is decomposed through self-similar agent structures.
- **Separation of Concerns**: Core infrastructure (`core/`) is strictly decoupled from domain agents (`agents/`).
- **Deterministic Fallbacks**: Agents operate gracefully even when external LLM endpoints are unavailable.
"""

FILES["CODE_STRUCTURE.md"] = """# Code Structure & Directory Map

```text
├── config.yaml               # System configuration
├── main.py                   # Application entrypoint
├── app.py                    # Application lifecycle harness
├── cli.py                    # Multi-command CLI tool
├── core/                     # Foundational abstractions
│   ├── agent_base.py         # BaseAgent abstract class
│   ├── orchestrator.py       # Task coordinator
│   ├── registry.py           # Agent registry
│   ├── task_queue.py         # Priority task queue
│   ├── state_manager.py      # Checkpoint manager
│   ├── communication.py      # Messaging & Stigmergy
│   ├── quality_gate.py       # Quality gate validation
│   ├── monitor.py            # Telemetry monitor
│   ├── sandbox.py            # Sandboxed execution
│   └── exceptions.py         # Core exceptions
├── agents/                   # Domain agent implementations
│   ├── planning/             # Planning Layer (P1-P10)
│   ├── coding/               # Coding Layer (C1-C24)
│   ├── testing/              # Testing Layer (T1-T16)
│   ├── security/             # Security Layer (S1-S12)
│   ├── quality/              # Quality Layer (Q1-Q12)
│   ├── infrastructure/       # Infrastructure Layer (I1-I14)
│   ├── commstate/            # CommState Layer (CS1-CS14)
│   ├── monitoring/           # Monitoring Layer (M1-M14)
│   └── documentation/        # Documentation Layer (D1-D12)
├── integration/              # Integration & Assembly Layer (IA1-IA14)
├── tests/                    # Testing & Validation Layer (TV1-TV14) & Unit Tests
└── docs/                     # Documentation Suite
```
"""

FILES["EXTENSION_GUIDE.md"] = """# Extension & Custom Agent Guide

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
"""

FILES["CONTRIBUTING.md"] = """# Contributing Guidelines

1. **Fork and Branch**: Create feature branches named `feature/your-feature`.
2. **Adhere to Code Standards**: Follow PEP 8 and include type annotations.
3. **Write Unit Tests**: Add tests to `tests/test_<domain>.py` maintaining >=80% coverage.
4. **Pass Regression**: Ensure `python -m unittest discover -s tests -t .` passes with 0 failures.
5. **Open Pull Request**: Detail the architectural justification and attach test results.
"""

FILES["DEBUGGING_GUIDE.md"] = """# Debugging Guide

### 1. Enable Verbose Logging
Run with `-v` or configure `config.yaml`:
```yaml
system:
  log_level: "DEBUG"
```

### 2. Inspect Checkpoint Snapshots
If an agent fails, examine:
`state/checkpoints/<timestamp>_<session_id>/agent_states.json`

### 3. Replay Engine
Use `ReplayEngine` (in `agents/commstate/replay_engine.py`) to reproduce execution step-by-step.
"""

# ==============================================================================
# 21-27: Installation & Deployment Files
# ==============================================================================

FILES["INSTALLATION.md"] = """# Installation Guide

## Step-by-Step Installation
1. **Clone Repository**:
   ```bash
   git clone https://github.com/fractal-core/fractal-system.git
   cd fractal-system
   ```
2. **Create Python Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: .\\venv\\Scripts\\activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Initialize Configuration**:
   ```bash
   cp config.example.yaml config.yaml
   ```
5. **Verify Installation**:
   ```bash
   python cli.py status
   ```
"""

FILES["PREREQUISITES.md"] = """# System Prerequisites

- **Python**: Version 3.10 or higher.
- **Operating System**: Linux (Ubuntu 20.04+), macOS (12+), or Windows 10/11.
- **Memory (RAM)**: Minimum 8 GB required (16 GB recommended).
- **Disk Space**: At least 5 GB free for logs, checkpoints, and dependencies.
- **Optional LLM Endpoint**: Ollama running locally (`ollama serve`) with `qwen2.5-coder:3b` model.
"""

FILES["VERIFICATION.md"] = """# Verification Guide

To verify your installation:

```bash
# 1. Run cluster health check
python cli.py health

# 2. Run system unit test regression suite
python -m unittest discover -s tests -t .

# 3. Test a live task execution
python main.py --task "Verify system functionality" --capability "integration"
```
All checks must report `OK` or `PASSED`.
"""

FILES["DEPLOYMENT.md"] = """# Deployment Guide

The Fractal system supports multiple deployment profiles:
- **Local / Developer**: Standalone process via `app.py` or `cli.py`.
- **Docker Container**: Single or multi-container deployment via Docker Compose.
- **Kubernetes Cluster**: Production deployment with horizontal pod autoscaling.
- **Cloud Managed**: AWS ECS, GCP Cloud Run, or Azure Container Instances.
"""

FILES["DOCKER_DEPLOYMENT.md"] = """# Docker Deployment

### Build Image
```bash
docker build -t fractal-core:latest .
```

### Run Container
```bash
docker run -d --name fractal-app \\
  -p 8000:8000 \\
  -v $(pwd)/state:/app/state \\
  -v $(pwd)/config.yaml:/app/config.yaml \\
  fractal-core:latest
```

### Docker Compose
```bash
docker-compose up -d
```
"""

FILES["K8S_DEPLOYMENT.md"] = """# Kubernetes Deployment

### Apply Manifests
```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
```

### Check Rollout Status
```bash
kubectl rollout status deployment/fractal-core-deployment
```
"""

FILES["CLOUD_DEPLOYMENT.md"] = """# Cloud Deployment

### AWS (ECS / EKS)
Deploy container to AWS ECR and run on Fargate task definition with 4 vCPU / 8 GB RAM.

### Google Cloud (Cloud Run / GKE)
```bash
gcloud run deploy fractal-service \\
  --image gcr.io/PROJECT_ID/fractal-core:latest \\
  --memory 8Gi --cpu 4
```

### Azure (Container Instances)
Deploy using Azure CLI pointing to Azure Container Registry (ACR).
"""

# ==============================================================================
# 28-31: Configuration Documentation Files
# ==============================================================================

FILES["CONFIGURATION.md"] = """# Configuration Guide

All configuration is managed through `config.yaml`.

```yaml
system:
  max_memory_mb: 8192
  max_global_depth: 7
  log_level: "INFO"

llm:
  endpoint: "http://localhost:11434"
  model: "qwen2.5-coder:3b"
  timeout_seconds: 30

orchestrator:
  worker_threads: 4
  task_timeout_seconds: 60

quality_gates:
  strict_mode: true
  min_pass_score: 80.0
```
"""

FILES["ENVIRONMENT_VARIABLES.md"] = """# Environment Variables

| Variable | Description | Default |
|---|---|---|
| `FRACTAL_CONFIG_PATH` | Path to custom YAML configuration file | `config.yaml` |
| `FRACTAL_ENV` | Environment (`development`, `staging`, `production`) | `development` |
| `FRACTAL_LOG_LEVEL` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |
| `OLLAMA_HOST` | Remote URL for Ollama inference server | `http://localhost:11434` |
| `FRACTAL_MAX_RAM` | Maximum memory limit in MB | `8192` |
"""

FILES["CUSTOM_CONFIG.md"] = """# Custom Configuration Profiles

### Development (`config.dev.yaml`)
- Verbose debug logging.
- Memory threshold: 4096 MB.
- Local SQLite database.

### Production (`config.prod.yaml`)
- Info level logging.
- Strict quality gates.
- Memory threshold: 8192 MB.
- Redis-backed message mailbox.
"""

FILES["VALIDATION.md"] = """# Configuration Validation

The system enforces validation rules on boot:
1. `max_memory_mb` must be between 1024 and 16384 MB.
2. `max_global_depth` must not exceed 7.
3. Quality gate scores must be between 0.0 and 100.0.
"""

# ==============================================================================
# 32-35: Agent Reference Files
# ==============================================================================

FILES["AGENT_REFERENCE.md"] = """# Agent Reference Catalog

The system includes 100+ specialized agents spanning 12 distinct layers:
1. **Planning**: P1 to P10
2. **Coding**: C1 to C24
3. **Testing**: T1 to T16
4. **Security**: S1 to S12
5. **Quality**: Q1 to Q12
6. **Infrastructure**: I1 to I14
7. **CommState**: CS1 to CS14
8. **Monitoring**: M1 to M14
9. **Integration**: IA1 to IA14
10. **Testing & Validation**: TV1 to TV14
11. **Documentation**: D1 to D12
"""

FILES["AGENT_CAPABILITIES.md"] = """# Agent Capabilities Index

| Agent ID | Name | Layer | Primary Capability |
|---|---|---|---|
| `P1_INTENT_CLARIFIER` | Intent Clarifier | Planning | `intent_clarification` |
| `C1_BACKEND_AGENT` | Backend Agent | Coding | `backend_development` |
| `T1_TEST_ORCHESTRATOR` | Test Orchestrator | Testing | `test_orchestration` |
| `S1_SECURITY_ORCHESTRATOR` | Security Orchestrator | Security | `security_orchestration` |
| `Q1_QUALITY_ORCHESTRATOR` | Quality Orchestrator | Quality | `quality_orchestration` |
| `I1_INFRA_ORCHESTRATOR` | Infrastructure Orchestrator | Infrastructure | `infrastructure_orchestration` |
| `CS1_COMMSTATE_ORCHESTRATOR` | CommState Orchestrator | CommState | `commstate_orchestration` |
| `M1_MONITORING_ORCHESTRATOR` | Monitoring Orchestrator | Monitoring | `monitoring_orchestration` |
| `IA1_INTEGRATION_ORCHESTRATOR` | Integration Orchestrator | Integration | `integration_orchestration` |
| `TV1_TEST_ORCHESTRATOR` | Test Orchestrator | Testing & Validation | `testing_validation` |
| `D1_DOC_ORCHESTRATOR` | Documentation Orchestrator | Documentation | `documentation` |
"""

FILES["AGENT_LIFECYCLE.md"] = """# Agent Lifecycle Protocol

All agents implement the four-stage state machine:
```mermaid
stateDiagram-v2
    [*] --> INITIALIZE
    INITIALIZE --> PROCESS
    PROCESS --> VALIDATE
    VALIDATE --> CLEANUP
    CLEANUP --> [*]
```
1. **INITIALIZE**: Allocate local buffers, register tools, unpack task envelopes.
2. **PROCESS**: Execute logic, spawn child subagents if needed.
3. **VALIDATE**: Audit outputs against schemas and quality gate thresholds.
4. **CLEANUP**: Release transient memory, remove temporary files, emit completion signals.
"""

FILES["CUSTOM_AGENT_GUIDE.md"] = """# How to Build Custom Agents

1. Subclass `BaseAgent` from `core.agent_base`.
2. Set `max_depth=2` to respect two-tier supervisory bounding.
3. Register domain tools using `self.register_tool()`.
4. Add custom capability strings to `self.capabilities`.
5. Register into `AgentRegistry`.
"""

# ==============================================================================
# 36-40: Examples Files
# ==============================================================================

FILES["EXAMPLES.md"] = """# Examples Catalog

Explore code examples across:
- **[Basic Examples](BASIC_EXAMPLES.md)**: Hello World, simple tasks.
- **[Advanced Examples](ADVANCED_EXAMPLES.md)**: Custom subagent hierarchies and quality gates.
- **[Use Case Examples](USE_CASE_EXAMPLES.md)**: Web apps, security hardening.
- **[Integration Examples](INTEGRATION_EXAMPLES.md)**: FastAPI gateway, CLI automation.
"""

FILES["BASIC_EXAMPLES.md"] = """# Basic Examples

### Example 1: Submit Single Task
```python
from core.orchestrator import Orchestrator

orch = Orchestrator()
orch.start()

task_id = orch.submit_task("Calculate Fibonacci numbers", capability="coding")
orch.wait_for_completion()
orch.stop()
```
"""

FILES["ADVANCED_EXAMPLES.md"] = """# Advanced Examples

### Example 2: Spawning Subagents
```python
from core.agent_base import BaseAgent

class ParentCoordinator(BaseAgent):
    def process(self, envelope):
        worker = self.spawn_subagent(BaseAgent, name="WorkerSubAgent")
        return worker.process(envelope)
```
"""

FILES["USE_CASE_EXAMPLES.md"] = """# Use Case Examples

### Example 3: Full Stack API Generation
Submit task:
```bash
python main.py --task "Generate complete user authentication REST API" --capability "coding"
```
Outputs controller, routes, database models, and unit tests.
"""

FILES["INTEGRATION_EXAMPLES.md"] = """# Integration Examples

### Example 4: CLI Status Query
```bash
python cli.py status
```
Inspects all active registered agents and cluster resource utilization.
"""

# ==============================================================================
# 41-45: Troubleshooting Files
# ==============================================================================

FILES["TROUBLESHOOTING.md"] = """# Troubleshooting Guide

When encountering issues:
1. Verify prerequisites in [PREREQUISITES.md](PREREQUISITES.md).
2. Check [COMMON_ISSUES.md](COMMON_ISSUES.md) for known edge cases.
3. Lookup error codes in [ERROR_CODES.md](ERROR_CODES.md).
4. Follow resolution steps in [SOLUTION_STEPS.md](SOLUTION_STEPS.md).
5. If unresolved, follow [ESCALATION_GUIDE.md](ESCALATION_GUIDE.md).
"""

FILES["COMMON_ISSUES.md"] = """# Common Operational Issues

### 1. LLM Connection Refused
- **Cause**: Ollama service is not running on port 11434.
- **Behavior**: System automatically switches to deterministic fallback mode.
- **Fix**: Run `ollama serve`.

### 2. Depth Limit Exceeded
- **Cause**: An agent attempted to spawn children beyond max depth.
- **Fix**: Check `max_depth` configuration.

### 3. RAM Limit Reached
- **Cause**: Total allocated agent memory exceeded 8192 MB.
- **Fix**: Clear idle agents or adjust `resources_mb` allocations.
"""

FILES["ERROR_CODES.md"] = """# Error Codes Reference

| Error Code | Error Name | Description |
|---|---|---|
| `ERR_001` | `AgentSpawnError` | Subagent failed during instantiation |
| `ERR_002` | `DepthExceededError` | Attempted to exceed global depth ceiling (7) |
| `ERR_003` | `ResourceQuotaExceededError` | RAM budget exceeded 8192 MB |
| `ERR_004` | `QualityGateFailure` | Artifact failed quality gate threshold |
| `ERR_005` | `TaskTimeoutError` | Task did not finish within timeout window |
| `ERR_006` | `CheckpointCorruptError` | State checkpoint failed integrity hash |
"""

FILES["SOLUTION_STEPS.md"] = """# Solution Steps

### Fixing Quality Gate Failures
1. Inspect quality score in `logs/app.log`.
2. Check specific check (e.g. `complexity` or `coverage`).
3. Refactor code or lower strictness threshold in `config.yaml`.
"""

FILES["ESCALATION_GUIDE.md"] = """# Issue Escalation Guide

1. Collect current state checkpoint from `state/checkpoints/`.
2. Export logs via `python cli.py health`.
3. File an issue on GitHub with reproduction steps.
"""

# ==============================================================================
# 46-50: FAQ Files
# ==============================================================================

FILES["FAQ.md"] = """# Frequently Asked Questions (FAQ)

- **[General FAQ](GENERAL_FAQ.md)**: Project scope, licensing, overview.
- **[Technical FAQ](TECHNICAL_FAQ.md)**: Stigmergy, fractal hierarchy, concurrency.
- **[Configuration FAQ](CONFIGURATION_FAQ.md)**: YAML settings, environment variables.
- **[Troubleshooting FAQ](TROUBLESHOOTING_FAQ.md)**: Common errors and solutions.
"""

FILES["GENERAL_FAQ.md"] = """# General FAQ

### What is the Fractal Multi-Agent Coding System?
An autonomous software engineering framework that solves tasks by decomposing them through self-similar agent hierarchies.

### What license is this released under?
The project is licensed under the open-source MIT License.
"""

FILES["TECHNICAL_FAQ.md"] = """# Technical FAQ

### Why use stigmergy instead of direct agent messaging?
Direct messaging between $N$ agents causes $O(N^2)$ communication bottlenecks. Stigmergy allows agents to coordinate indirectly through blackboard signals, scaling linearly.

### What is the maximum depth?
The global depth is bounded at Level 7, with a two-tier supervisory rule (Parent -> Child -> Grandchild).
"""

FILES["CONFIGURATION_FAQ.md"] = """# Configuration FAQ

### How do I change the memory limit?
Set `max_memory_mb: 8192` in `config.yaml` or export `FRACTAL_MAX_RAM=8192`.

### Can I run without an external LLM?
Yes! The system includes deterministic fallback handlers for all agents.
"""

FILES["TROUBLESHOOTING_FAQ.md"] = """# Troubleshooting FAQ

### Why did my task complete with deterministic output?
Ollama was unreachable at `http://localhost:11434`, so the system executed in deterministic fallback mode to ensure progress without crashing.

### How do I reset the system state?
Run `python cli.py health` or remove contents of `state/checkpoints/`.
"""


def main():
    os.makedirs(DOCS_DIR, exist_ok=True)
    count = 0
    for filename, content in FILES.items():
        filepath = os.path.join(DOCS_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        count += 1
        print(f"[{count}/50] Generated: {filepath}")
    print(f"Successfully generated all {count} documentation files in {DOCS_DIR}")


if __name__ == "__main__":
    main()
