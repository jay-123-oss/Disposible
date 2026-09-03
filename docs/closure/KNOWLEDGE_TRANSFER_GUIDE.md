# Knowledge Transfer & Operations Handover Guide

**Target Audience:** SREs, DevOps Engineers, and System Administrators  
**Facilitator:** KnowledgeTransferManager (FC10)  

---

## 1. System Architecture Overview
The system utilizes a 3-tier hierarchy:
1. **L3 Orchestrators:** Direct domain coordinators (`ProductionMonitoringOrchestrator`, `FinalClosureOrchestrator`, etc.).
2. **L4 Coordinators:** Functional managers (`RealTimeMonitor`, `QualityAuditor`, etc.).
3. **L5 Atomic Workers:** Focused execution subagents executing specific tasks (`LatencyMonitor`, `CodeQualityAuditor`, etc.).

## 2. Daily Operational Commands
- **Start System Daemon / Task:**
  ```bash
  python main.py --task "Run routine system audit" --capability "quality_audit"
  ```
- **Inspect System Health:**
  ```bash
  python -m cli.fractal_cli health
  ```
- **Execute Regression Suite:**
  ```bash
  python -m unittest discover -s tests -t .
  ```
- **Initiate Emergency Rollback:**
  ```bash
  python final_integration/rollback.py --target-version v1.0.0-GA
  ```

## 3. Configuration Management
- Primary settings: `config.yaml`
- Monitoring rules: `monitoring_support/monitoring_config.yaml`
- Alert rules: `monitoring_support/alerts/alert_rules.yaml`
- Runbooks: `monitoring_support/runbooks/`
