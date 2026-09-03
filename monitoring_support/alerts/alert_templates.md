# Alert Message Templates

## Critical Severity Template (PagerDuty / Slack)
```text
🚨 [CRITICAL ALERT] {{ alert_name }}
Environment: Production
Component: {{ component }}
Metric Value: {{ actual_value }} (Threshold: {{ threshold_value }})
Started: {{ start_time }}
Incident Ticket: {{ ticket_id }}
Runbook: https://ops.fractal-system.internal/runbooks/{{ alert_name }}
Escalation: Level {{ escalation_tier }} On-Call
```

## High / Medium Severity Template (Slack / Email)
```text
⚠️ [ALERT - {{ severity }}] {{ alert_name }}
Component: {{ component }}
Details: {{ summary }}
Current Value: {{ actual_value }}
Recommended Action: Inspect {{ component }} logs and auto-scaling events.
```
