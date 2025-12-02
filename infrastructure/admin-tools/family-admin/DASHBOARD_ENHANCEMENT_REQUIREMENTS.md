# Dashboard Enhancement Requirements

## Current Status
The dashboard (`/dashboard`) has basic functionality but can be significantly enhanced with Phase 2 system monitoring and family statistics. The frontend is ready for enhancement while backend connectivity issues are being resolved.

## Available Phase 2 Endpoints ✅
The following endpoints are confirmed working and can be integrated into the dashboard:

### 1. Phase 2 System Health
**Endpoint**: `GET /api/phase2/health`
**Status**: ✅ Working (tested from admin frontend context)

**Response Structure**:
```json
{
  "status": "healthy|degraded|unhealthy",
  "layers": {
    "redis": {
      "status": "healthy",
      "latency_ms": 5.726
    },
    "mem0": {
      "status": "healthy",
      "latency_ms": 0.0002
    },
    "qdrant": {
      "status": "healthy",
      "latency_ms": 7.359,
      "collections": 3
    }
  },
  "overall_latency_ms": 13.092,
  "error_rate": 0.0,
  "timestamp": "2025-01-20T21:33:46.497695"
}
```

### 2. System Statistics
**Endpoint**: `GET /api/phase2/stats`
**Status**: ⚠️ Available but needs testing

### 3. Core System Prompt
**Endpoint**: `GET /api/phase2/prompts/core`
**Status**: ✅ Working (tested successfully)

## Proposed Dashboard Enhancements

### 1. Phase 2 System Health Widget
**Location**: Top of dashboard, prominent position
**Content**: Real-time health status of 5-layer memory system

**Features**:
- ✅ Overall system status with color coding
- ✅ Individual layer health indicators
- ✅ Latency metrics for each layer
- ✅ Real-time refresh capability
- ✅ Historical uptime visualization

**Design**:
```jsx
<div className="grid grid-cols-1 md:grid-cols-4 gap-4">
  {/* Overall Status */}
  <div className="bg-white rounded-lg p-4 border">
    <h3>System Status</h3>
    <div className={`text-2xl font-bold ${
      health.status === 'healthy' ? 'text-green-600' :
      health.status === 'degraded' ? 'text-yellow-600' : 'text-red-600'
    }`}>
      {health.status.toUpperCase()}
    </div>
  </div>

  {/* Redis Layer */}
  <div className="bg-white rounded-lg p-4 border">
    <h4>Redis</h4>
    <div className="text-sm text-gray-600">Latency: {health.layers.redis.latency_ms}ms</div>
  </div>

  {/* Mem0 Layer */}
  <div className="bg-white rounded-lg p-4 border">
    <h4>Working Memory</h4>
    <div className="text-sm text-gray-600">Latency: {health.layers.mem0.latency_ms}ms</div>
  </div>

  {/* Qdrant Layer */}
  <div className="bg-white rounded-lg p-4 border">
    <h4>Vector Store</h4>
    <div className="text-sm text-gray-600">Collections: {health.layers.qdrant.collections}</div>
  </div>
</div>
```

### 2. Knowledge Base Statistics
**Source**: Knowledge management system (`/knowledge`)
**Integration**: Pull statistics from knowledge management hook

**Metrics**:
- Total knowledge documents
- Active documents count
- Categories breakdown
- Word count totals
- Last updated timestamp

### 3. Family Activity Overview
**Source**: Family management system (`/family`)
**Integration**: Pull data from family management hook

**Metrics**:
- Total family members
- Active members (last 24h)
- Parental controls status
- Screen time usage summary

### 4. Prompt System Overview
**Source**: System prompt management (`/chat`)
**Integration**: Pull data from prompt management hook

**Metrics**:
- Core prompt status
- Active role prompts
- Prompt build statistics
- Last prompt update

### 5. System Performance Metrics
**Source**: Phase 2 system monitoring
**Integration**: Direct API calls to working endpoints

**Metrics**:
- API response times
- Error rates
- Service uptime
- Memory usage (if available)

## Implementation Priority

### Phase 1: Immediate (High Priority)
1. ✅ **Phase 2 Health Widget** - Use existing working endpoint
2. ⚠️ **System Performance Dashboard** - Integrate `/api/phase2/stats`
3. 📋 **Knowledge Base Summary** - Connect to existing knowledge management

### Phase 2: Enhancement (Medium Priority)
1. 🔄 **Family Activity Overview** - Enhance with backend data when available
2. 🔧 **Prompt System Overview** - Connect to existing prompt management
3. 📊 **Historical Data Visualization** - Add time-series charts

### Phase 3: Advanced (Low Priority)
1. 📈 **Advanced Analytics** - Custom metrics and insights
2. 🔔 **Real-time Alerts** - System health notifications
3. 📱 **Mobile Responsive** - Optimize for mobile viewing

## Technical Requirements

### 1. Hook Creation
Create dashboard-specific hooks:
- `useSystemHealth.ts` - Phase 2 health monitoring
- `useKnowledgeStats.ts` - Knowledge management statistics
- `useFamilyActivity.ts` - Family activity overview
- `usePromptStats.ts` - Prompt system metrics

### 2. Component Development
Create reusable dashboard widgets:
- `SystemHealthWidget.tsx` - Phase 2 health display
- `KnowledgeStatsWidget.tsx` - Knowledge metrics
- `FamilyActivityWidget.tsx` - Family overview
- `PromptStatsWidget.tsx` - Prompt system stats

### 3. Integration Points
- ✅ API calls to existing working endpoints
- ⚠️ Error handling for backend connectivity issues
- 🔄 Real-time data refresh capabilities
- 📊 Loading states and error boundaries

## Current Dashboard Files
- **Main Page**: `src/app/(admin)/dashboard/page.tsx`
- **Hook**: `src/hooks/useDashboardData.ts`
- **API Client**: `src/lib/api-client.ts` (Phase 2 methods available)

## Success Criteria
1. ✅ Phase 2 system health monitoring integrated
2. ✅ Real-time system status display
3. ✅ Knowledge management statistics
4. ✅ Family activity overview (when backend available)
5. ✅ Responsive design for all screen sizes
6. ✅ Graceful degradation when backend unavailable

## Mock Data for Development
While backend connectivity is being resolved, implement mock data for:
- System health status variations
- Knowledge document statistics
- Family member activity
- Prompt system usage patterns

---

**Status**: Ready for implementation
**Dependencies**: Phase 2 endpoints confirmed working
**Blockers**: None - can proceed with mock data and real endpoints