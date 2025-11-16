# Deployment Rollback Procedures

**Purpose**: Systematic rollback procedures for Family Assistant and Python services
**Target**: Production deployments with minimal downtime
**Updated**: 2025-11-15

---

## 🚨 Emergency Rollback Procedure

### Immediate Response (0-5 minutes)

#### 1. Identify Deployment Issue
```bash
# Check pod status
kubectl get pods -n homelab -l app=family-assistant

# Check recent deployments
kubectl rollout history deployment/family-assistant -n homelab

# Check pod logs
kubectl logs -n homelab deployment/family-assistant --tail=50
```

#### 2. Quick Health Assessment
```bash
# Test basic API functionality
curl -f http://100.81.76.55:30080/health || echo "❌ Health check failed"

# Test dashboard endpoint
curl -f http://100.81.76.55:30080/dashboard/system-health || echo "❌ Dashboard failed"
```

#### 3. Immediate Rollback Command
```bash
# Rollback to previous revision
kubectl rollout undo deployment/family-assistant -n homelab

# Watch rollback progress
kubectl rollout status deployment/family-assistant -n homelab --timeout=300s
```

#### 4. Verify Rollback Success
```bash
# Check pod status after rollback
kubectl get pods -n homelab -l app=family-assistant

# Verify API functionality
curl -f http://100.81.76.55:30080/health && echo "✅ Rollback successful"
```

---

## 🔄 Standard Rollback Procedure

### Pre-Rollback Assessment

#### 1. Determine Rollback Target
```bash
# View deployment history
kubectl rollout history deployment/family-assistant -n homelab

# Get revision details
kubectl rollout history deployment/family-assistant -n homelab --revision=3

# Choose target revision (usually previous stable version)
TARGET_REVISION=3  # Adjust based on history
```

#### 2. Assess Impact
```bash
# Check current error rate
kubectl logs -n homelab deployment/family-assistant --since=10m | grep -i error

# Check user impact (if monitoring available)
curl -s "http://100.81.76.55:30080/dashboard/system-health" | jq '.alerts'
```

#### 3. Prepare Rollback Communication
```bash
# Create rollback incident
echo "Rollback initiated: $(date)" >> /var/log/deployment-rollbacks.log
echo "Reason: <specific reason>" >> /var/log/deployment-rollbacks.log
echo "Target revision: $TARGET_REVISION" >> /var/log/deployment-rollbacks.log
```

### Execute Rollback

#### 1. Backup Current State
```bash
# Save current deployment configuration
kubectl get deployment family-assistant -n homelab -o yaml > /tmp/family-assistant-current.yaml

# Save current service configuration
kubectl get service family-assistant -n homelab -o yaml > /tmp/family-assistant-service.yaml

# Document rollback reason
cat > /tmp/rollback-reason.txt << EOF
Rollback Reason: <detailed description>
Timestamp: $(date)
Trigger: <automatic/manual>
Impact Assessment: <affected users/features>
EOF
```

#### 2. Perform Rollback
```bash
# Execute rollback to specific revision
kubectl rollout undo deployment/family-assistant -n homelab --to-revision=$TARGET_REVISION

# Monitor rollback progress
kubectl rollout status deployment/family-assistant -n homelab
```

#### 3. Validate Rollback
```bash
# Wait for new pods to be ready
kubectl wait --for=condition=available --timeout=300s deployment/family-assistant -n homelab

# Test API functionality
curl -f http://100.81.76.55:30080/health
curl -f http://100.81.76.55:30080/dashboard/system-health

# Test core functionality (sample requests)
curl -X POST http://100.81.76.55:30080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "user_id": "test_user"}'
```

---

## 🛠️ Advanced Rollback Scenarios

### Scenario 1: Database Migration Issues
```bash
# Identify failed migration
kubectl logs -n homelab deployment/family-assistant | grep -i migration

# Rollback application (keep database as-is)
kubectl rollout undo deployment/family-assistant -n homelab

# Check database compatibility
kubectl exec -it deployment/family-assistant -n homelab -- \
  python -c "
import asyncpg
import asyncio

async def check_db():
    conn = await asyncpg.connect('postgresql://user:pass@postgres:5432/db')
    # Test critical queries
    await conn.fetchval('SELECT COUNT(*) FROM user_profiles')
    print('✅ Database compatible')
    await conn.close()

asyncio.run(check_db())
"
```

### Scenario 2: Configuration Issues
```bash
# Check current configmaps
kubectl get configmap -n homelab | grep family-assistant

# Restore previous configmap if needed
kubectl apply -f /path/to/previous-configmap.yaml

# Restart deployment
kubectl rollout restart deployment/family-assistant -n homelab
```

### Scenario 3: External Service Dependencies
```bash
# Check external service connectivity
kubectl exec -it deployment/family-assistant -n homelab -- \
  curl -f http://ollama.homelab.svc.cluster.local:11434/api/tags

# If external service down, rollback to version with fallbacks
kubectl rollout undo deployment/family-assistant -n homelab
```

---

## 📊 Rollback Automation Scripts

### Quick Rollback Script
```bash
#!/bin/bash
# rollback.sh - Quick rollback to previous version

set -e

NAMESPACE="homelab"
DEPLOYMENT="family-assistant"

echo "🔄 Starting rollback for $DEPLOYMENT..."

# Check current status
echo "Current deployment status:"
kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT

# Get previous revision
PREV_REVISION=$(kubectl rollout history deployment/$DEPLOYMENT -n $NAMESPACE | tail -2 | head -1 | awk '{print $1}')
echo "Rolling back to revision: $PREV_REVISION"

# Perform rollback
kubectl rollout undo deployment/$DEPLOYMENT -n $NAMESPACE --to-revision=$PREV_REVISION

# Wait for rollout
echo "Waiting for rollout to complete..."
kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=300s

# Verify rollback
echo "Verifying rollback..."
kubectl wait --for=condition=available --timeout=60s deployment/$DEPLOYMENT -n $NAMESPACE

# Test API
if curl -f http://100.81.76.55:30080/health > /dev/null 2>&1; then
    echo "✅ Rollback successful!"
else
    echo "❌ Rollback failed - health check not passing"
    exit 1
fi

echo "🎉 Rollback completed successfully!"
```

### Comprehensive Rollback Script
```bash
#!/bin/bash
# comprehensive-rollback.sh - Full rollback with validation

set -e

NAMESPACE="homelab"
DEPLOYMENT="family-assistant"
SERVICE_PORT="30080"
BACKUP_DIR="/tmp/rollback-$(date +%Y%m%d-%H%M%S)"

mkdir -p $BACKUP_DIR

echo "🔄 Comprehensive rollback for $DEPLOYMENT"
echo "Backup directory: $BACKUP_DIR"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Step 1: Pre-rollback backup
log "Creating backup of current deployment..."
kubectl get deployment $DEPLOYMENT -n $NAMESPACE -o yaml > $BACKUP_DIR/deployment.yaml
kubectl get service $DEPLOYMENT -n $NAMESPACE -o yaml > $BACKUP_DIR/service.yaml
kubectl get configmap -n $NAMESPACE -o yaml > $BACKUP_DIR/configmaps.yaml

# Step 2: Health check before rollback
log "Assessing current health..."
CURRENT_HEALTH=$(curl -s http://100.81.76.55:$SERVICE_PORT/health 2>/dev/null || echo "FAILED")
if [[ "$CURRENT_HEALTH" == "FAILED" ]]; then
    log "❌ Current deployment unhealthy - proceeding with rollback"
else
    log "⚠️ Current deployment appears healthy - confirm rollback needed"
    read -p "Continue with rollback? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Rollback cancelled"
        exit 0
    fi
fi

# Step 3: Get rollback target
log "Determining rollback target..."
ROLLBACK_TARGET=$(kubectl rollout history deployment/$DEPLOYMENT -n $NAMESPACE | grep "^[0-9]" | tail -2 | head -1 | awk '{print $1}')
log "Rolling back to revision: $ROLLBACK_TARGET"

# Step 4: Execute rollback
log "Executing rollback..."
kubectl rollout undo deployment/$DEPLOYMENT -n $NAMESPACE --to-revision=$ROLLBACK_TARGET

# Step 5: Monitor rollback progress
log "Monitoring rollback progress..."
kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=600s

# Step 6: Post-rollback validation
log "Performing post-rollback validation..."

# Wait for pods to be ready
kubectl wait --for=condition=available --timeout=120s deployment/$DEPLOYMENT -n $NAMESPACE

# Test API endpoints
log "Testing API endpoints..."

# Health check
for i in {1..5}; do
    if curl -f http://100.81.76.55:$SERVICE_PORT/health >/dev/null 2>&1; then
        log "✅ Health check passed (attempt $i)"
        break
    else
        log "⏳ Health check failed (attempt $i/5), waiting..."
        sleep 10
    fi
done

# Dashboard functionality
if curl -f http://100.81.76.55:$SERVICE_PORT/dashboard/system-health >/dev/null 2>&1; then
    log "✅ Dashboard endpoint working"
else
    log "⚠️ Dashboard endpoint not responding"
fi

# Core functionality test
log "Testing core functionality..."
RESPONSE=$(curl -s -X POST http://100.81.76.55:$SERVICE_PORT/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "rollback test", "user_id": "test_user"}' 2>/dev/null || echo "FAILED")

if [[ "$RESPONSE" == *"response"* ]]; then
    log "✅ Core functionality working"
else
    log "⚠️ Core functionality may be impaired"
fi

# Step 7: Generate rollback report
cat > $BACKUP_DIR/rollback-report.txt << EOF
ROLLBACK REPORT
================
Timestamp: $(date)
Deployment: $DEPLOYMENT
Namespace: $NAMESPACE
Target Revision: $ROLLBACK_TARGET

BEFORE ROLLBACK:
- Health Status: $CURRENT_HEALTH
- Pod Status: $(kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT --no-headers | wc -l) pods

AFTER ROLLBACK:
- Health Status: $(curl -s http://100.81.76.55:$SERVICE_PORT/health 2>/dev/null || echo "FAILED")
- Pod Status: $(kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT --no-headers | wc -l) pods

BACKUP FILES:
- deployment.yaml
- service.yaml
- configmaps.yaml

NEXT STEPS:
1. Investigate root cause of deployment failure
2. Test fixes in staging environment
3. Update deployment pipeline with additional checks
4. Consider canary deployments for critical services
EOF

log "✅ Rollback completed successfully!"
log "📁 Backup and report saved to: $BACKUP_DIR"
log "📋 View rollback report: cat $BACKUP_DIR/rollback-report.txt"
```

---

## 🔍 Rollback Decision Matrix

### When to Rollback Immediately
| Condition | Severity | Action |
|----------|---------|--------|
| API completely down (5xx errors) | Critical | Immediate rollback |
| Database connection failures | Critical | Immediate rollback |
| Authentication not working | Critical | Immediate rollback |
> 50% error rate | High | Immediate rollback |
| Response time > 10 seconds | High | Immediate rollback |
| Memory leaks detected | High | Immediate rollback |
| Security vulnerability detected | Critical | Immediate rollback |

### When to Monitor Before Rolling Back
| Condition | Severity | Monitoring Period | Action |
|----------|---------|-----------------|--------|
| < 10% error rate | Medium | 5-10 minutes | Monitor, rollback if worsening |
| Slight performance degradation | Low | 15-30 minutes | Monitor, rollback if sustained |
| Non-critical feature broken | Low | 30-60 minutes | Monitor, rollback if impacting users |
| Minor UI issues | Low | 1-2 hours | Monitor, schedule fix |

### When Not to Rollback
- Minor configuration issues that can be hot-fixed
- Cosmetic UI problems
| Performance improvements with initial instability |
| Non-breaking feature additions with minor bugs |

---

## 📋 Rollback Communication Template

### Slack/Teams Notification
```markdown
🚨 **DEPLOYMENT ROLLBACK ALERT**

**Service**: Family Assistant API
**Environment**: Production
**Time**: $(date)
**Duration**: ~2 minutes
**Impact**: Users may have experienced brief API errors

**What Happened**:
Deployment [version] caused [issue description]
Rolled back to previous stable version [revision]

**Current Status**: ✅ Service restored and healthy
**Next Steps**:
- Investigating root cause
- Planning fix for next deployment
- Additional testing before redeploy

**Questions**: Contact @devops-team
```

### Email Notification
```markdown
Subject: PRODUCTION ROLLBACK: Family Assistant API - Service Restored

Team,

A rollback was performed on the Family Assistant API deployment.

Details:
- Time: $(date)
- Duration: 2 minutes
- Issue: [Brief description of the problem]
- Action: Rolled back to previous stable version
- Current Status: Service operational

Impact:
- Brief API interruptions occurred between [start_time] and [end_time]
- All services have been restored to normal operation

Next Steps:
1. Root cause analysis in progress
2. Fix will be implemented and tested in staging
3. Additional monitoring has been enabled

Please monitor your applications and report any unusual behavior.

Best regards,
DevOps Team
```

---

## 🧪 Rollback Testing

### Test Rollback Procedure
```bash
#!/bin/bash
# test-rollback.sh - Test rollback procedures in staging

echo "🧪 Testing rollback procedures in staging..."

# Deploy test version
echo "Deploying test version..."
kubectl apply -f family-assistant-test.yaml -n staging

# Wait for deployment
kubectl wait --for=condition=available deployment/family-assistant -n staging --timeout=300s

# Test rollback
echo "Testing rollback to previous version..."
kubectl rollout undo deployment/family-assistant -n staging

# Verify rollback success
kubectl rollout status deployment/family-assistant -n staging --timeout=300s

echo "✅ Rollback test completed successfully"
```

### Rollback Drill Schedule
- **Monthly**: Test rollback procedures in staging
- **Quarterly**: Full rollback drill with communication simulation
- **After major incidents**: Review and improve rollback procedures

---

## 📈 Rollback Metrics to Track

1. **MTTR (Mean Time to Recovery)**: Time from issue detection to service restoration
2. **Rollback Frequency**: How often rollbacks are needed
3. **Rollback Success Rate**: Percentage of rollbacks that successfully restore service
4. **Time to Detection**: How quickly issues are identified
5. **User Impact**: Number of users affected by deployment issues

### Metrics Collection
```bash
# Log rollback events
echo "$(date),rollback,$DEPLOYMENT,$TARGET_REVISION,$DURATION_MINUTES" >> /var/log/rollback-metrics.log

# Calculate MTTR
awk -F',' '/rollback/ { sum+=$5; count++ } END { print "Average MTTR:", sum/count, "minutes" }' /var/log/rollback-metrics.log
```

---

## 🔄 Post-Rollback Actions

### Immediate Actions (0-1 hour after rollback)
1. **Verify Service Health**: Ensure all endpoints are responding correctly
2. **Monitor Error Rates**: Watch for any continued issues
3. **User Communication**: Notify users that service is restored
4. **Team Debrief**: Quick discussion of what went wrong

### Short-term Actions (1-24 hours after rollback)
1. **Root Cause Analysis**: Investigate why the deployment failed
2. **Fix Development**: Address the issues that caused the rollback
3. **Enhanced Testing**: Add tests to prevent similar issues
4. **Update Procedures**: Improve deployment and rollback procedures

### Long-term Actions (1 week after rollback)
1. **Process Review**: Evaluate deployment pipeline effectiveness
2. **Architecture Review**: Consider if changes needed to prevent similar issues
3. **Training**: Team training on improved procedures
4. **Documentation Updates**: Update all relevant documentation

---

## 🛡️ Prevention Strategies

### Deployment Improvements
1. **Canary Deployments**: Roll out to small subset of users first
2. **Blue-Green Deployments**: Maintain parallel production environments
3. **Feature Flags**: Deploy code behind flags, enable gradually
4. **Automated Testing**: Comprehensive pre-deployment testing

### Monitoring Enhancements
1. **Real-time Alerting**: Immediate notification of issues
2. **Performance Baselines**: Know what "normal" looks like
3. **Automated Health Checks**: Continuous API endpoint monitoring
4. **User Experience Monitoring**: Track actual user impact

### Process Improvements
1. **Peer Reviews**: All deployments reviewed by team members
2. **Staging Environment**: Mirror production environment exactly
3. **Deployment Checklists**: Ensure no steps are missed
4. **Post-Deployment Monitoring**: Dedicated monitoring after each deployment

---

**Remember**: Rollbacks are not failures - they're safety mechanisms that protect user experience. The goal is to make them rare, fast, and reliable. 🚀✨