# Best Practices Guide

1. **Be Specific in Intents**: Instead of "Fix backend", prompt "Fix user session timeout handling in auth middleware".
2. **Explicit Capabilities**: Specify `--capability` (e.g. `coding`, `testing_validation`, `security`) to accelerate routing.
3. **Monitor Memory**: Ensure total agent allocations do not exceed the 8192 MB global cap.
4. **Run Verification Before Commits**: Execute `python -m unittest discover -s tests -t .` regularly.
5. **Leverage Cleanups**: Always allow graceful shutdowns so checkpoints are cleanly persisted.
