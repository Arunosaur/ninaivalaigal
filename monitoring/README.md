# Observability Package (Multipart Security)

This bundle contains Grafana dashboards, Prometheus recording rules, and alert rules pre-wired to your hardened multipart metrics.

## Files
- `monitoring/grafana_dashboards/multipart_security_main.json` — main service dashboard
- `monitoring/grafana_dashboards/multipart_security_alerts.json` — alerts overview dashboard
- `monitoring/prometheus-recording-rules.yml` — SLO & helper recording rules
- `monitoring/prometheus-alerts.yml` — sample alert rules

## Setup
1. **Prometheus**  
   Load `prometheus-recording-rules.yml` and `prometheus-alerts.yml` in your Prometheus config.
2. **Grafana**  
   Import the two JSON dashboards and set the datasource to your Prometheus instance (uid `prom` by default).
3. **Metrics expected**
   - `multipart_reject_total{reason}` (bounded reasons)
   - `multipart_parts_total`, `multipart_bytes_total`
   - `archive_ratio_max`, `archive_entries_total`
   - `strict_mode_flag` (0/1)
   - `http_request_duration_seconds_bucket{endpoint="/upload"}`

## SLOs (baseline)
- Upload success rate ≥ **99.9%**
- Added P95 latency from adapter ≤ **5 ms**
- False-positive reject rate ≤ **0.1%**

## Notes
- You can scope alerts to canary by appending label filters (e.g., `cluster=~"canary|prod"`).
- For per-tenant noise reduction, use the recording rule `slo:upload_rejects_per_tenant:rate` and set thresholds relative to tenant baseline.
