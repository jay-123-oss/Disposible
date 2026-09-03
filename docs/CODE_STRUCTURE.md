# Code Structure & Directory Map

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
