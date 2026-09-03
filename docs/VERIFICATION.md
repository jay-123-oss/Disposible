# Verification Guide

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
