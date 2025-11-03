# Notification Setup Guide (US#102 - AC8)

This guide explains how to set up Slack and Email notifications for Prometheus alerts.

## Overview

Prometheus alerts are configured in `/monitoring/alerts.yml`. Notifications are handled by Alertmanager (if deployed) or Grafana's built-in alerting system.

## Option 1: Grafana Built-in Alerting (Recommended for US#102)

Grafana has built-in alerting that can send notifications directly.

### Slack Integration

1. **Create Slack Webhook**:
   - Go to https://api.slack.com/apps
   - Create a new app or use existing
   - Enable "Incoming Webhooks"
   - Create webhook URL

2. **Configure in Grafana**:
   - Navigate to: Alerting > Notification channels
   - Add new channel
   - Type: Slack
   - Webhook URL: `https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK`
   - Channel: `#alerts` or `#monitoring`
   - Save

3. **Create Alert Rules in Grafana**:
   - Navigate to: Alerting > Alert rules
   - Create new rule based on Prometheus queries
   - Set notification channel to Slack
   - Save

### Email Integration

1. **Configure SMTP in Grafana**:
   - Navigate to: Administration > Settings > SMTP
   - Configure SMTP settings:
     ```
     Host: smtp.gmail.com:587
     User: your-email@gmail.com
     Password: <app-password>
     From Address: alerts@ninaivalaigal.com
     ```

2. **Create Email Notification Channel**:
   - Alerting > Notification channels
   - Type: Email
   - Addresses: ops-team@example.com
   - Save

3. **Link to Alert Rules**:
   - Create alert rules in Grafana
   - Add email channel to notifications

## Option 2: Alertmanager (Advanced)

If you prefer using Prometheus Alertmanager:

1. **Deploy Alertmanager**:
   ```bash
   container run -d --name ninaivalaigal-dev-alertmanager \
     -p 9093:9093 \
     -v $(pwd)/config/prometheus/alertmanager.yml:/etc/alertmanager/alertmanager.yml \
     prom/alertmanager:latest
   ```

2. **Update Prometheus Config**:
   ```yaml
   alerting:
     alertmanagers:
       - static_configs:
           - targets:
               - 'alertmanager:9093'
   ```

3. **Configure Receivers** in `alertmanager.yml` (see `config/prometheus/alertmanager.yml`)

## Alert Rules Summary

Current alert rules in `/monitoring/alerts.yml`:

1. **HighErrorRate** - Error rate > 0.1% (SLO violation)
2. **HighP95Latency** - P95 latency > 200ms (SLO violation)
3. **LowAvailability** - Availability < 99.9% (SLO violation)
4. **SLORisk** - SLO metrics approaching thresholds
5. **ServiceDown** - Service unavailable
6. **HighCPU** - CPU usage > 85%
7. **HighMemory** - Memory usage > 4GB

## Testing Notifications

1. **Test Slack**:
   ```bash
   curl -X POST http://localhost:3001/api/alerts/test \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Alert", "message": "This is a test"}'
   ```

2. **Test Email**:
   - Create a test alert rule in Grafana
   - Manually trigger it
   - Verify email receipt

## Next Steps

- [ ] Set up Slack webhook URL
- [ ] Configure Grafana notification channels
- [ ] Create alert rules in Grafana UI
- [ ] Test notification delivery
- [ ] Document team notification preferences

---

**Developer F** - 2025-11-02
