# Production Rollback Procedures

## 1. When to Initiate Rollback
- Post-deployment error rate > 5% for more than 5 minutes.
- Latency P95 > 500ms under nominal traffic.
- Data inconsistency or unrecoverable schema migration issue.
- Smoke tests fail after production deployment switchover.

## 2. Automated Rollback Execution
Run the automated rollback script immediately:
```bash
python rollback.py
```

## 3. Post-Rollback Validation
Verify that the rollback succeeded and restored nominal operations:
```bash
python verify_deployment.py
python smoke_test.py
```

## 4. Post-Rollback Incident Management
1. Update status page: "Rollback completed. System operating on previous stable version."
2. Preserve container logs and core dumps for root cause analysis.
3. Convene incident debrief with Engineering Lead and SRE.
