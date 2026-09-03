# Debugging Guide

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
