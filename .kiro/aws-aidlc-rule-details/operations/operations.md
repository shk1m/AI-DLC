# Operations

**Purpose**: Deploy, monitor, and maintain each unit's services in production environments.

**Focus**: How to DEPLOY, RUN, and MAINTAIN the system

**Stages in OPERATIONS PHASE**:
- Deployment Planning (ALWAYS)
- Monitoring & Observability Setup (ALWAYS)
- Maintenance & Support (ALWAYS)

## Prerequisites
- Build and Test must be complete for all units being deployed
- Infrastructure Design artifacts must be available
- Code Generation must be complete with deployment artifacts (Dockerfile, K8s manifests, IaC)

---

# DEPLOYMENT PLANNING

## Step 1: Analyze Deployment Context
- Read infrastructure design from `aidlc-docs/construction/{unit-name}/infrastructure-design/`
- Read deployment architecture from `aidlc-docs/construction/{unit-name}/infrastructure-design/deployment-architecture.md`
- Identify deployment dependencies between units
- Determine deployment order based on unit dependency graph

## Step 2: Create Deployment Plan
- Generate plan with checkboxes [] for deployment execution
- Focus on environment provisioning, service deployment order, validation gates
- Each step should have a checkbox []

## Step 3: Generate Context-Appropriate Questions
**DIRECTIVE**: Analyze the infrastructure design and deployment architecture to identify ALL areas where clarification would improve deployment quality and safety.

**CRITICAL**: Default to asking questions when there is ANY ambiguity about deployment targets, rollback procedures, or production readiness criteria.

- EMBED questions using [Answer]: tag format
- Focus on deployment safety, rollback strategy, and production readiness

**Question categories to evaluate**:
- **Deployment Targets** - Ask about target environments, deployment windows, and change management
- **Rollback Strategy** - Ask about rollback triggers, automated vs manual rollback, and data migration rollback
- **Production Readiness** - Ask about pre-deployment checklists, smoke tests, and canary criteria
- **Deployment Order** - Ask about service dependency order, blue-green vs rolling, and traffic shifting
- **Data Migration** - Ask about schema migrations, data backfill, and backward compatibility
- **Feature Flags** - Ask about gradual rollout, feature toggles, and A/B testing needs

## Step 4: Store Plan
- Save as `aidlc-docs/operations/plans/{unit-name}-deployment-plan.md`
- Include all [Answer]: tags for user input

## Step 5: Collect and Analyze Answers
- Wait for user to complete all [Answer]: tags
- **MANDATORY**: Review ALL responses for vague or ambiguous answers
- Create clarification questions if ANY ambiguities are detected
- **Do not proceed until ALL ambiguities are resolved**

## Step 6: Generate Deployment Artifacts
- Create `aidlc-docs/operations/{unit-name}/deployment/deployment-runbook.md`
- Create `aidlc-docs/operations/{unit-name}/deployment/rollback-procedures.md`
- Create `aidlc-docs/operations/{unit-name}/deployment/production-readiness-checklist.md`

### Deployment Runbook Template
```markdown
# Deployment Runbook — [unit-name]

## Pre-Deployment Checklist
- [ ] All tests passing in CI pipeline
- [ ] Infrastructure provisioned (CDK/Terraform applied)
- [ ] Database migrations tested in staging
- [ ] Secrets configured in target environment
- [ ] Monitoring dashboards ready
- [ ] Rollback procedure reviewed
- [ ] On-call team notified

## Deployment Steps

### 1. Infrastructure Provisioning
[IaC deployment commands]

### 2. Database Migration
[Migration execution steps with validation]

### 3. Service Deployment
[Container/K8s deployment commands with health checks]

### 4. Post-Deployment Validation
[Smoke tests, health checks, metric verification]

### 5. Traffic Shifting (if applicable)
[Canary/blue-green traffic shifting steps]

## Rollback Triggers
- Error rate > [X]% for [Y] minutes
- Latency p95 > [X]ms for [Y] minutes
- Health check failures > [X] consecutive
- Critical alert fired

## Rollback Steps
[Step-by-step rollback procedure]
```

### Rollback Procedures Template
```markdown
# Rollback Procedures — [unit-name]

## Automated Rollback
- **Trigger**: [Conditions that trigger automatic rollback]
- **Mechanism**: [How automated rollback works]
- **Notification**: [Who gets notified]

## Manual Rollback

### Application Rollback
[Steps to roll back application code]

### Database Rollback
[Steps to roll back schema changes — if applicable]

### Infrastructure Rollback
[Steps to roll back infrastructure changes]

## Post-Rollback Actions
- [ ] Verify service health
- [ ] Check data integrity
- [ ] Notify stakeholders
- [ ] Create incident report
- [ ] Schedule root cause analysis
```

### Production Readiness Checklist Template
```markdown
# Production Readiness Checklist — [unit-name]

## Reliability
- [ ] Health check endpoints implemented (/health, /ready)
- [ ] Graceful shutdown configured
- [ ] Circuit breakers configured for external dependencies
- [ ] Retry logic with exponential backoff
- [ ] Dead letter queues for failed messages
- [ ] Multi-AZ deployment

## Observability
- [ ] Structured logging configured
- [ ] Distributed tracing enabled
- [ ] Custom metrics exposed
- [ ] Dashboards created
- [ ] Alerts configured (Critical/Warning/Info)
- [ ] SLO/SLI defined and tracked

## Security
- [ ] Secrets stored in Secrets Manager (no hardcoded credentials)
- [ ] IAM roles follow least privilege
- [ ] Network security groups configured
- [ ] Encryption at rest and in transit
- [ ] Input validation on all endpoints
- [ ] Access logging enabled

## Scalability
- [ ] Auto-scaling policies configured (HPA/Cluster Autoscaler)
- [ ] Resource requests and limits set
- [ ] Connection pooling configured
- [ ] Cache layer operational
- [ ] Load testing completed and targets met

## Operations
- [ ] Runbook documented
- [ ] Rollback procedure tested
- [ ] On-call rotation established
- [ ] Incident response plan defined
- [ ] Backup and restore tested
```

## Step 7: Present Completion Message

```markdown
# 🚀 Deployment Planning Complete - [unit-name]

> **📋 <u>**REVIEW REQUIRED:**</u>**  
> Please examine the deployment artifacts at: `aidlc-docs/operations/[unit-name]/deployment/`

> **🚀 <u>**WHAT'S NEXT?**</u>**
>
> **You may:**
>
> 🔧 **Request Changes** - Ask for modifications to the deployment plan
> ✅ **Continue to Next Stage** - Approve and proceed to **Monitoring & Observability Setup**

---
```

## Step 8: Wait for Explicit Approval
- Do not proceed until the user explicitly approves
- If user requests changes, update and repeat

## Step 9: Record Approval and Update Progress
- Log approval in audit.md with timestamp
- Mark Deployment Planning complete in aidlc-state.md

---

# MONITORING & OBSERVABILITY SETUP

## Step 10: Analyze Monitoring Requirements
- Read NFR requirements from `aidlc-docs/construction/{unit-name}/nfr-requirements/`
- Read NFR design (observability patterns) from `aidlc-docs/construction/{unit-name}/nfr-design/`
- Identify SLOs, SLIs, and alerting requirements

## Step 11: Generate Context-Appropriate Questions

**Question categories to evaluate**:
- **SLO Targets** - Ask about service level objectives, error budgets, and burn rate alerts
- **Alerting Strategy** - Ask about alert routing, escalation paths, and on-call schedules
- **Dashboard Requirements** - Ask about operational vs business dashboards, audience, and refresh rates
- **Log Retention** - Ask about log retention policies, compliance requirements, and cost constraints
- **Incident Classification** - Ask about severity levels, response times, and escalation criteria

## Step 12: Generate Monitoring Artifacts
- Create `aidlc-docs/operations/{unit-name}/monitoring/slo-definitions.md`
- Create `aidlc-docs/operations/{unit-name}/monitoring/alerting-rules.md`
- Create `aidlc-docs/operations/{unit-name}/monitoring/dashboards.md`
- Create `aidlc-docs/operations/{unit-name}/monitoring/log-management.md`

### SLO Definitions Template
```markdown
# SLO Definitions — [unit-name]

## Service Level Indicators (SLIs)

| SLI | Measurement | Data Source |
|---|---|---|
| Availability | Successful requests / Total requests | CloudWatch |
| Latency | p95 response time | X-Ray |
| Throughput | Requests per second | Prometheus |
| Error Rate | 5xx responses / Total responses | ALB Access Logs |

## Service Level Objectives (SLOs)

| SLO | Target | Window | Error Budget |
|---|---|---|---|
| Availability | 99.99% | 30 days | 4.32 minutes/month |
| Latency (p95) | < 200ms | 30 days | — |
| Error Rate | < 0.01% | 30 days | — |
| Data Freshness | < 60 minutes | Rolling | — |

## Error Budget Policy
- **Budget remaining > 50%**: Normal development velocity
- **Budget remaining 25-50%**: Increased testing, slower rollouts
- **Budget remaining < 25%**: Feature freeze, focus on reliability
- **Budget exhausted**: Deployment freeze until budget recovers
```

### Alerting Rules Template
```markdown
# Alerting Rules — [unit-name]

## Critical Alerts (Page immediately)
| Alert | Condition | Action |
|---|---|---|
| Service Down | Health check fails > 3 consecutive | Page on-call, auto-restart |
| SLO Burn Rate High | Error budget burn > 10x normal | Page on-call |
| Database Unreachable | DB connection fails > 30s | Page on-call |
| Collection Pipeline Stopped | No successful collection > 2 hours | Page on-call |

## Warning Alerts (Notify, no page)
| Alert | Condition | Action |
|---|---|---|
| High Error Rate | 5xx > 1% for 5 minutes | Slack notification |
| Latency Degradation | p95 > 500ms for 10 minutes | Slack notification |
| Source Failures | 3+ consecutive source failures | Slack notification |
| Cache Hit Rate Low | Hit rate < 80% for 15 minutes | Slack notification |

## Info Alerts (Log only)
| Alert | Condition | Action |
|---|---|---|
| New Item Discovered | Unmapped item code found | Log + dashboard |
| Source Reactivated | Previously failed source recovers | Log |
| Model Retrain Triggered | Scheduled model retraining | Log |

## Escalation Path
1. **L1 (On-call engineer)**: Respond within 5 minutes for Critical
2. **L2 (Team lead)**: Escalate if unresolved after 15 minutes
3. **L3 (Engineering manager)**: Escalate if unresolved after 30 minutes
```

### Dashboards Template
```markdown
# Dashboards — [unit-name]

## Operational Dashboard (Engineering Team)
- Service health status (all pods)
- Request rate and error rate
- Latency percentiles (p50, p95, p99)
- Collection pipeline status (per source)
- Circuit breaker states
- Queue depths (SQS)
- Cache hit/miss ratio
- DB connection pool utilization

## Business Dashboard (Stakeholders)
- Data freshness (last successful collection per source)
- Item coverage (tracked items vs total available)
- Source availability (uptime per source)
- NLP analysis throughput
- Knowledge graph growth metrics

## SLO Dashboard (SRE/Platform)
- SLO compliance (current vs target)
- Error budget remaining
- Burn rate trends
- Incident timeline
```

## Step 13: Present Completion Message

```markdown
# 📊 Monitoring & Observability Complete - [unit-name]

> **📋 <u>**REVIEW REQUIRED:**</u>**  
> Please examine the monitoring artifacts at: `aidlc-docs/operations/[unit-name]/monitoring/`

> **🚀 <u>**WHAT'S NEXT?**</u>**
>
> **You may:**
>
> 🔧 **Request Changes** - Ask for modifications to the monitoring setup
> ✅ **Continue to Next Stage** - Approve and proceed to **Maintenance & Support**

---
```

## Step 14: Wait for Explicit Approval
- Do not proceed until the user explicitly approves
- If user requests changes, update and repeat

## Step 15: Record Approval and Update Progress
- Log approval in audit.md with timestamp
- Mark Monitoring & Observability complete in aidlc-state.md

---

# MAINTENANCE & SUPPORT

## Step 16: Analyze Maintenance Requirements
- Read all prior artifacts (design, code, infrastructure, monitoring)
- Identify maintenance scenarios (patching, scaling, data management)
- Determine support model (on-call, escalation, SLA)

## Step 17: Generate Context-Appropriate Questions

**Question categories to evaluate**:
- **Patching Strategy** - Ask about OS/dependency update frequency, testing requirements, and rollout approach
- **Scaling Procedures** - Ask about manual scaling triggers, capacity planning, and cost optimization
- **Data Management** - Ask about data retention, archival, purging, and compliance requirements
- **Incident Response** - Ask about incident classification, response SLAs, and post-mortem process
- **Change Management** - Ask about change approval process, maintenance windows, and communication
- **Disaster Recovery** - Ask about DR testing frequency, failover procedures, and recovery validation

## Step 18: Generate Maintenance Artifacts
- Create `aidlc-docs/operations/{unit-name}/maintenance/maintenance-runbook.md`
- Create `aidlc-docs/operations/{unit-name}/maintenance/incident-response.md`
- Create `aidlc-docs/operations/{unit-name}/maintenance/capacity-planning.md`
- Create `aidlc-docs/operations/{unit-name}/maintenance/disaster-recovery.md`

### Maintenance Runbook Template
```markdown
# Maintenance Runbook — [unit-name]

## Routine Maintenance

### Daily
- [ ] Review overnight alerts and resolve
- [ ] Check collection pipeline success rate
- [ ] Verify data freshness across all sources
- [ ] Review DLQ for failed messages

### Weekly
- [ ] Review SLO compliance and error budget
- [ ] Check dependency vulnerability scan results
- [ ] Review and resolve unmapped item codes
- [ ] Verify backup integrity

### Monthly
- [ ] Apply security patches (OS, dependencies)
- [ ] Review and optimize resource allocation
- [ ] Capacity planning review
- [ ] Cost optimization review
- [ ] DR drill (quarterly)

## Common Operational Procedures

### Scaling Up
[Steps to manually scale service]

### Adding a New Data Source
[Steps to configure and activate a new source]

### Rotating Secrets
[Steps to rotate API keys and credentials]

### Database Maintenance
[Vacuum, reindex, statistics update procedures]

### Log Investigation
[Common log queries for troubleshooting]
```

### Incident Response Template
```markdown
# Incident Response — [unit-name]

## Severity Classification

| Severity | Definition | Response Time | Resolution Target |
|---|---|---|---|
| SEV-1 (Critical) | Service completely down, data loss risk | 5 minutes | 30 minutes |
| SEV-2 (High) | Major feature degraded, SLO at risk | 15 minutes | 2 hours |
| SEV-3 (Medium) | Minor feature impacted, workaround exists | 1 hour | 8 hours |
| SEV-4 (Low) | Cosmetic issue, no user impact | Next business day | 5 business days |

## Incident Workflow

1. **Detect**: Alert fires or user reports issue
2. **Triage**: Classify severity, assign responder
3. **Investigate**: Gather data, identify root cause
4. **Mitigate**: Apply immediate fix or workaround
5. **Resolve**: Implement permanent fix
6. **Review**: Post-mortem within 48 hours (SEV-1/2)

## Common Incident Scenarios

### Collection Pipeline Failure
- **Symptoms**: No new data for > 1 hour
- **Investigation**: Check CronJob status, Pod logs, source availability
- **Mitigation**: Restart CronJob, check circuit breaker states
- **Resolution**: Fix root cause (source API change, credential expiry, etc.)

### Database Connection Exhaustion
- **Symptoms**: 5xx errors, connection timeout logs
- **Investigation**: Check PgBouncer stats, active connections
- **Mitigation**: Kill idle connections, scale PgBouncer
- **Resolution**: Optimize connection usage, increase pool size

### Memory/CPU Spike
- **Symptoms**: Pod OOMKilled, high latency
- **Investigation**: Check resource usage, identify memory leak
- **Mitigation**: Restart affected pods, scale horizontally
- **Resolution**: Fix memory leak, adjust resource limits

## Post-Mortem Template
- **Incident ID**: [ID]
- **Duration**: [Start - End]
- **Impact**: [Users/services affected]
- **Root Cause**: [What caused the incident]
- **Timeline**: [Chronological events]
- **Action Items**: [Preventive measures with owners and deadlines]
```

### Capacity Planning Template
```markdown
# Capacity Planning — [unit-name]

## Current Utilization

| Resource | Current | Limit | Utilization |
|---|---|---|---|
| CPU (avg) | [X] cores | [Y] cores | [Z]% |
| Memory (avg) | [X] GB | [Y] GB | [Z]% |
| Storage (Timestream) | [X] GB | Auto | — |
| Storage (RDS) | [X] GB | [Y] GB | [Z]% |
| Network (egress) | [X] GB/month | — | — |

## Growth Projections

| Metric | Current | 6 months | 12 months | Action Needed |
|---|---|---|---|---|
| Items tracked | [X] | [Y] | [Z] | [Scale plan] |
| Data points/hour | [X] | [Y] | [Z] | [Scale plan] |
| Storage (total) | [X] GB | [Y] GB | [Z] GB | [Tier plan] |
| API requests/sec | [X] | [Y] | [Z] | [Scale plan] |

## Scaling Triggers
- CPU utilization > 70% sustained → Add nodes
- Memory utilization > 80% → Increase limits or add replicas
- Storage > 80% capacity → Expand or archive
- Queue depth > 1000 sustained → Add consumers

## Cost Optimization
- Right-size instances based on actual utilization
- Use Spot instances for non-critical workloads (NLP workers)
- Implement Timestream tiering (hot → cold)
- Review and remove unused resources monthly
```

### Disaster Recovery Template
```markdown
# Disaster Recovery — [unit-name]

## DR Strategy
- **Approach**: Backup & Restore
- **RPO**: 24 hours (daily snapshots)
- **RTO**: 30 minutes (snapshot restore + service restart)

## Backup Inventory

| Resource | Backup Method | Frequency | Retention | Location |
|---|---|---|---|---|
| RDS | Automated snapshot | Daily | 35 days | Same region |
| Neptune | Automated snapshot | Daily | 35 days | Same region |
| Redis | Automated backup | Daily | 7 days | Same region |
| Timestream | Built-in (Magnetic) | Continuous | 5 years | Same region |
| IaC Code | Git | Every commit | Permanent | GitHub |
| Secrets | Secrets Manager | Versioned | Permanent | Same region |

## Recovery Procedures

### Scenario 1: Single Service Failure
1. Kubernetes auto-restarts Pod
2. If persistent: `kubectl rollout undo deployment/{name}`
3. Verify health checks pass

### Scenario 2: Database Corruption
1. Identify corruption scope
2. Restore from latest clean snapshot
3. Replay events from SQS DLQ if needed
4. Verify data integrity

### Scenario 3: Full Region Failure
1. Activate cross-region DR (if configured)
2. Update DNS to DR region
3. Verify all services operational
4. Communicate to stakeholders

## DR Testing Schedule
- **Monthly**: Backup restore verification (automated)
- **Quarterly**: Full DR drill (manual failover simulation)
- **Annually**: Full region failover test
```

## Step 19: Present Completion Message

```markdown
# 🔧 Maintenance & Support Complete - [unit-name]

> **📋 <u>**REVIEW REQUIRED:**</u>**  
> Please examine the maintenance artifacts at: `aidlc-docs/operations/[unit-name]/maintenance/`

> **🚀 <u>**WHAT'S NEXT?**</u>**
>
> **You may:**
>
> 🔧 **Request Changes** - Ask for modifications to the maintenance procedures
> ✅ **Approve & Complete** - Approve maintenance plan (Operations Phase complete for this unit)

---
```

## Step 20: Wait for Explicit Approval
- Do not proceed until the user explicitly approves
- If user requests changes, update and repeat

## Step 21: Record Approval and Update Progress
- Log approval in audit.md with timestamp
- Mark Operations Phase complete for this unit in aidlc-state.md
- Update overall workflow status

---

## Key Principles

- **Per-Unit Execution**: Operations stages execute for each unit independently
- **Dependency Order**: Deploy units in dependency order (base services first)
- **Safety First**: Always have rollback procedures before deploying
- **Observability Before Traffic**: Monitoring must be operational before serving production traffic
- **Runbook-Driven**: All operational procedures documented in runbooks
- **Blameless Post-Mortems**: Focus on systemic improvements, not individual blame
- **Automation Priority**: Automate repetitive operational tasks where possible
- **Cost Awareness**: Include cost monitoring and optimization in maintenance cycles

## Directory Structure

```text
aidlc-docs/
├── operations/
│   ├── plans/
│   │   └── {unit-name}-deployment-plan.md
│   ├── {unit-name}/
│   │   ├── deployment/
│   │   │   ├── deployment-runbook.md
│   │   │   ├── rollback-procedures.md
│   │   │   └── production-readiness-checklist.md
│   │   ├── monitoring/
│   │   │   ├── slo-definitions.md
│   │   │   ├── alerting-rules.md
│   │   │   ├── dashboards.md
│   │   │   └── log-management.md
│   │   └── maintenance/
│   │       ├── maintenance-runbook.md
│   │       ├── incident-response.md
│   │       ├── capacity-planning.md
│   │       └── disaster-recovery.md
│   └── shared/
│       ├── on-call-schedule.md
│       └── communication-plan.md
```

## Integration with Core Workflow

### State Tracking Updates
When Operations stages execute, update `aidlc-docs/aidlc-state.md`:

```markdown
### 🟡 OPERATIONS PHASE
- [x] Deployment Planning - {unit-name}
- [x] Monitoring & Observability - {unit-name}
- [x] Maintenance & Support - {unit-name}
```

### Audit Logging
All Operations stage interactions must be logged in `aidlc-docs/audit.md` following the standard format:

```markdown
## Operations - [Stage Name] - [unit-name]
**Timestamp**: [ISO timestamp]
**User Input**: "[Complete raw user input]"
**AI Response**: "[AI's response or action taken]"
**Context**: OPERATIONS - [Stage], [unit-name]

---
```
