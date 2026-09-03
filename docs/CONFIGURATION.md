# Configuration Guide

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
