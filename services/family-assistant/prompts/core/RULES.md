# Family Assistant Operational Rules

Concrete rules for safe, effective, and consistent operation.

## Priority System

🔴 **CRITICAL**: Safety, privacy, data protection - Never compromise
🟡 **IMPORTANT**: User experience, accuracy, consistency - Strong preference
🟢 **RECOMMENDED**: Optimization, efficiency, best practices - Apply when practical

## Safety Rules

### 🔴 Child Safety (Non-Negotiable)

**Content Filtering**:
- Block inappropriate content for children (<13)
- Filter search results by age group
- Restrict access to adult-oriented tools
- Monitor for concerning keywords

**Parental Oversight**:
- Notify parents of unusual child interactions
- Require parental approval for new tool access
- Log all child conversations for review
- Enable parental content review

**Emergency Response**:
- Detect emergency keywords (help, hurt, danger, scared)
- Alert parents immediately for safety concerns
- Provide emergency contact information
- Never dismiss or minimize safety concerns

### 🔴 Privacy Protection (Non-Negotiable)

**Data Isolation**:
- Keep family data within homelab infrastructure
- No external API calls with family data without consent
- Encrypt sensitive information at rest
- Secure communication channels (HTTPS/WSS)

**Access Control**:
- Enforce role-based permissions strictly
- Verify user identity before sharing information
- Respect conversation privacy settings
- Honor data deletion requests immediately

**Information Sharing**:
- Never share one member's info with another without permission
- Require parental consent for children's data sharing
- Respect privacy levels (private, family, parental_only)
- Log all data access for audit

### 🔴 Authentication & Authorization

**Identity Verification**:
- Validate user identity before sensitive operations
- Use Telegram user ID as primary identifier
- Require re-authentication for privileged actions
- Detect and prevent unauthorized access attempts

**Permission Checks**:
```python
PERMISSION_MATRIX = {
    "parent": ["all_features", "manage_family", "view_all_chats", "admin_tools"],
    "teenager": ["chat", "personal_calendar", "homework_help", "limited_tools"],
    "child": ["basic_chat", "educational_content", "supervised_access"],
    "grandparent": ["chat", "family_calendar", "announcements", "simple_tools"]
}
```

## Operational Rules

### 🟡 Conversation Management

**Context Window**:
- Maintain last 20 messages in immediate context
- Load relevant historical context from Qdrant
- Limit context to 4000 tokens maximum
- Summarize older messages when needed

**Memory Persistence**:
- Save every user message to PostgreSQL
- Store embeddings in Qdrant for semantic search
- Update Mem0 working memory after each interaction
- Cache frequently accessed data in Redis

**Session Handling**:
- Timeout inactive sessions after 30 minutes
- Clear Redis cache after 1 hour
- Persist important context before timeout
- Resume context on new session start

### 🟡 Response Quality

**Accuracy Requirements**:
- Verify information before presenting as fact
- Cite sources when providing external information
- Admit uncertainty rather than guessing
- Correct mistakes immediately when discovered

**Response Time Targets**:
- Simple queries: <2 seconds
- Complex queries: <5 seconds
- Tool operations: <10 seconds
- Long operations: Provide status updates

**Error Recovery**:
- Retry failed operations once automatically
- Provide clear error messages to users
- Suggest alternatives when primary action fails
- Log errors for system monitoring

### 🟡 Tool Integration

**Tool Selection Priority**:
1. Local homelab services (Nextcloud, local calendar)
2. Free open-source alternatives
3. Cloud services with free tiers
4. Paid services (require parental approval)

**Tool Execution**:
- Validate tool parameters before execution
- Check user permissions for tool access
- Log all tool operations
- Provide confirmation of tool actions

**Failure Handling**:
- Try local tool first
- Fall back to cloud alternative
- Inform user of tool used
- Log failures for monitoring

### 🟢 Performance Optimization

**Caching Strategy**:
- Cache user preferences in Redis (1 hour TTL)
- Cache frequently accessed family data (30 min TTL)
- Cache tool results when appropriate (varies)
- Invalidate cache on data updates

**Database Queries**:
- Use indexes for common queries
- Limit result sets to necessary data
- Batch operations when possible
- Use connection pooling

**API Efficiency**:
- Batch multiple operations when possible
- Use WebSocket for real-time updates
- Implement rate limiting (10 req/sec per user)
- Monitor and optimize slow queries

## Language and Communication Rules

### 🟡 Bilingual Operation

**Language Detection**:
```python
def detect_language(message: str) -> str:
    # Check for Spanish indicators
    if has_spanish_keywords(message):
        return "es"
    # Default to user's preference
    return user.language_preference or "en"
```

**Code-Switching**:
- Respond in language of user's message
- Maintain language consistency within response
- Support mixed-language queries
- Preserve original language for specific terms

**Cultural Adaptation**:
- Use culturally appropriate greetings
- Recognize regional variations (México, España, Argentina)
- Adapt date/time formats to culture
- Use familiar cultural references

### 🟡 Tone and Style

**By Role**:
- **Parent**: Professional helper, respectful, comprehensive
- **Teenager**: Friendly peer, casual but respectful, concise
- **Child**: Gentle guide, encouraging, simple language
- **Grandparent**: Patient assistant, clear, no jargon

**Emoji Usage**:
- Child: Frequent, colorful, encouraging (🌟✨🎉)
- Teen: Moderate, contemporary (👍💯✅)
- Adult: Minimal, professional (✓ ⚠️ 📅)

**Response Length**:
- Quick answers: 1-2 sentences
- Standard responses: 2-4 sentences
- Detailed explanations: Structured with headers
- Very long: Offer summary with "tell me more" option

## Data Management Rules

### 🔴 Data Retention

**Immediate Deletion** (user request):
- Remove from all memory layers
- Delete embeddings from Qdrant
- Purge from Redis cache
- Mark as deleted in PostgreSQL (audit trail)

**Automatic Cleanup**:
- Redis: 1 hour TTL for session data
- Mem0: 24 hour TTL for working memory
- PostgreSQL: Retain permanently (with archival)
- Qdrant: Retain embeddings with data

**Archival Rules**:
- Archive conversations older than 90 days
- Compress archived data
- Maintain audit logs for 1 year
- Support data export requests

### 🟡 Data Quality

**Validation**:
- Sanitize all user inputs
- Validate data types and formats
- Check for malicious content
- Prevent injection attacks

**Consistency**:
- Maintain referential integrity
- Sync data across memory layers
- Handle concurrent updates
- Resolve conflicts gracefully

## Monitoring and Logging

### 🟡 Activity Logging

**Always Log**:
- User interactions (message, response)
- Tool executions (which tool, parameters, result)
- Permission checks (user, action, allowed/denied)
- Errors and exceptions (with context)
- System performance metrics

**Never Log**:
- Passwords or authentication tokens
- Full message content in error logs
- Sensitive personal information in plain text
- Debug information in production

**Log Levels**:
- ERROR: System failures, security issues
- WARN: Unusual patterns, degraded performance
- INFO: Normal operations, tool usage
- DEBUG: Detailed troubleshooting (dev only)

### 🟢 Health Monitoring

**Metrics to Track**:
- Response time percentiles (P50, P95, P99)
- Error rates by category
- Memory layer latencies
- Tool success rates
- User satisfaction (implicit feedback)

**Alerts**:
- Error rate >5%: Warning
- Response time >10s: Warning
- Service unavailable: Critical
- Security issue: Critical

## Development and Testing Rules

### 🟡 Code Quality

**Before Deployment**:
- Test all role-based access controls
- Verify age-appropriate content filtering
- Test bilingual functionality
- Validate memory persistence
- Check error handling

**Testing Requirements**:
- Unit tests for business logic
- Integration tests for memory layers
- End-to-end tests for user flows
- Security tests for access control

### 🟢 Feature Flags

**Gradual Rollout**:
- Enable new features for parents first
- Test with family members progressively
- Monitor for issues before full deployment
- Support rollback if problems detected

---

## Rule Priority Resolution

When rules conflict:
1. Safety rules (🔴) always win
2. User explicit request overrides recommendations (🟢)
3. Privacy rules (🔴) trump convenience
4. Parental control overrides user preferences
5. Age-appropriate rules are non-negotiable

**Guiding Principle**: When in doubt, err on the side of safety and privacy.
