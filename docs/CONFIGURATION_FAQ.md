# Configuration FAQ

### How do I change the memory limit?
Set `max_memory_mb: 8192` in `config.yaml` or export `FRACTAL_MAX_RAM=8192`.

### Can I run without an external LLM?
Yes! The system includes deterministic fallback handlers for all agents.
