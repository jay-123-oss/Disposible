# Service & System Recovery Procedures

## 1. Agent Cluster Deadlock Recovery
If agent orchestration encounters cyclic stigmergic deadlocks or thread pool starvation:
```bash
python main.py --health
# Restart worker pool and reload state manager
python main.py --task "Purge stalled queues and rehydrate agents from latest checkpoint" --capability "state_management"
```

## 2. Memory Exhaustion Mitigation (> 8192 MB)
If the host or container approaches the 8GB ceiling:
1. Trigger automatic worker pool garbage collection:
   ```bash
   python -c "import gc; gc.collect()"
   ```
2. Prune old state checkpoints beyond the last 3 stable snapshots.
3. Scale horizontal agent workers if running in Kubernetes.

## 3. Network & Connection Pool Recovery
1. Verify database socket connectivity:
   ```bash
   python verify_deployment.py
   ```
2. Reset hung TCP connection pools and drain idle worker threads.
