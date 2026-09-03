# Incident Response Runbook

## 1. Overview & Triage (< 5 Minutes)
- Identify incident severity: `Critical` (system down or SLA breached), `High` (degraded latency/capacity), `Medium` (non-blocking errors), or `Low` (minor cosmetic/telemetry warnings).
- Acknowledge alert in PagerDuty or Slack `#production-alerts`.
- Verify monitoring dashboard: `monitoring_support/dashboards/system_dashboard.json`.

## 2. Response Coordination (< 15 Minutes)
- Assign Incident Commander (IC) and Communications Lead.
- Open dedicated war room channel `#inc-YYYYMMDD-id`.
- Notify stakeholders if severity is High or Critical.

## 3. Resolution Execution (< 60 Minutes)
- Execute targeted mitigation (restart service, scale pod replicas, isolate faulty agent, or restore state checkpoint).
- If resolution is not progressing within 30 minutes, evaluate triggering rollback procedures.

## 4. Verification & Incident Closure
- Validate telemetry has returned to nominal baseline:
  - Latency P95 < 200ms
  - Error rate < 1%
  - CPU/RAM < 80%
- Resolve PagerDuty incident and mark support tickets as `RESOLVED`.
- Schedule Root Cause Analysis (RCA) meeting within 24 hours.
