# Operational Handover & Operations Guide

## 1. System Overview
The Fractal Multi-Agent Autonomous Coding System operates as an autonomous multi-tier hierarchical swarm.
- **Entry Points:** `main.py` CLI, REPL interactive session, batch manifest runner, and REST API.
- **Root Configuration:** `config.yaml` with domain-specific sections (`production:`, `performance_testing:`, `uat:`, `final_integration:`).

## 2. Day-2 Operations Runbook
- **Health Verification:** `python verify_deployment.py`
- **Smoke Testing:** `python smoke_test.py`
- **Emergency Rollback:** `python rollback.py`
- **Cluster Status:** `python main.py --status`

## 3. Incident Management & Support Escalation
- **Level 1 (Monitoring):** Automatic alerts via Prometheus (port 9090) and Grafana.
- **Level 2 (SRE / Ops):** On-call response for circuit breaker trips and auto-scaler saturation.
- **Level 3 (Core Engineering):** Bug triage and code patching via git hotfix branch.

## 4. Maintenance & Backups
- **Daily Full Backup:** Scheduled at 02:00 UTC (`0 2 * * *`).
- **Incremental Snapshots:** Every 6 hours (`0 */6 * * *`).
- **Log Retention:** 30 days retention with 100MB automatic rotation and gzip compression.
