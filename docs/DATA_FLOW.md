# Data Flow Architecture

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
