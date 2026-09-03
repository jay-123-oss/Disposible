# Fractal Multi-Agent Coding System

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
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

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
