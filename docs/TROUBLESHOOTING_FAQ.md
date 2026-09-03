# Troubleshooting FAQ

### Why did my task complete with deterministic output?
Ollama was unreachable at `http://localhost:11434`, so the system executed in deterministic fallback mode to ensure progress without crashing.

### How do I reset the system state?
Run `python cli.py health` or remove contents of `state/checkpoints/`.
