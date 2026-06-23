# A.N.N. SOC 2 Type II Compliance Checklist

## Trust Service Criteria

### Security (Common Criteria)

- [ ] **CC1.1** — CISO role defined, security policies documented
- [ ] **CC2.1** — Information classification policy (public, internal, confidential, restricted)
- [ ] **CC3.1** — Risk assessment performed annually
- [ ] **CC4.1** — Monitoring controls in place (Prometheus, Grafana, alerting)
- [ ] **CC5.1** — Logical access controls (RBAC, API keys, JWT validation)
- [ ] **CC6.1** — System boundaries defined (network segmentation, VPC, security groups)
- [ ] **CC6.2** — Encryption at rest (RDS, S3, ElastiCache) and in transit (TLS 1.2+)
- [ ] **CC6.3** — Input validation on all API endpoints
- [ ] **CC6.6** — Vulnerability management (dependency scanning, WAF)
- [ ] **CC7.1** — Incident detection within 60 seconds
- [ ] **CC7.2** — Incident response plan documented and tested
- [ ] **CC7.3** — Incident communication plan (status page, stakeholder notification)
- [ ] **CC8.1** — Change management process (PR reviews, CI/CD gates)

### Availability

- [ ] **A1.1** — SLA definitions per tier (99% → 99.99%)
- [ ] **A1.2** — Capacity planning documented (HPA, auto-scaling)
- [ ] **A1.3** — Backup and recovery procedures (RDS snapshots, S3 versioning)
- [ ] **A1.4** — DR plan with multi-region failover tested quarterly

### Confidentiality

- [ ] **C1.1** — Data classification and handling procedures
- [ ] **C1.2** — Access restricted to authorized personnel (Supabase RLS)
- [ ] **C1.3** — Data retention and disposal policy (S3 lifecycle, log rotation)

### Privacy

- [ ] **P1.1** — Privacy notice published
- [ ] **P2.1** — Consent collected for data processing
- [ ] **P3.1** — PII collection minimized
- [ ] **P4.1** — PII usage limited to stated purposes
- [ ] **P6.1** — Data subject access request process
- [ ] **P7.1** — Third-party data sharing agreements (ElevenLabs, HeyGen, OpenAI)

## Implementation Status

| Area | Status | Owner | Target Date |
|------|--------|-------|-------------|
| Access Controls | In Progress | Backend Team | Sprint 34 |
| Encryption | Complete | Infra | Sprint 22 |
| Monitoring | Complete | Infra | Sprint 24 |
| Incident Response | Draft | Security | Sprint 35 |
| Data Residency | Planned | Infra | Sprint 34 |
| Audit Logging | Complete | Backend | Sprint 26 |
| Penetration Test | Planned | External | Sprint 35 |

## Data Residency Options

| Region | Infrastructure | Compliance |
|--------|---------------|------------|
| US (us-east-1) | Primary | SOC 2, CCPA |
| EU (eu-west-1) | Secondary | GDPR, SOC 2 |
| India (ap-south-1) | Tertiary | IT Act 2000 |

## Audit Evidence Collection

Evidence is automatically collected from:
- Git commit history (change management)
- CI/CD pipeline logs (deployment controls)
- Prometheus/Grafana (monitoring evidence)
- Audit log table (access and moderation decisions)
- AWS CloudTrail (infrastructure access)
- Supabase audit logs (database access)
