# Common Operational Issues

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
