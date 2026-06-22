# Monitoring & Observability

Centralized monitoring, logging, and alerting.

## Stack
- **Metrics**: Prometheus + Grafana dashboards
- **Logging**: Structured logs (structlog) → Loki or ELK
- **Tracing**: OpenTelemetry (planned)
- **Alerting**: Grafana alerting rules + PagerDuty/Slack

## Dashboards (planned)
- API latency and error rates per service
- Pipeline throughput and success rates
- Agent performance scoring
- Media generation queue depth
