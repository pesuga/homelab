# Backend Integration Plan - Family Assistant Admin Panel

## Overview

This document outlines the integration plan for connecting the Next.js admin panel with the FastAPI backend Phase 2 API endpoints.

## Current State

### Frontend Pages Created
1. **Home/Dashboard** (`/`) - Already integrated with basic backend
2. **Family Shared Knowledge** (`/knowledge`) - Mock data
3. **MCP & Tool Connections** (`/mcp`) - Mock data
4. **MyFamily** (`/family`) - Mock data (4 tabs: Members, Controls, Features, Reports)
5. **General Settings** (`/settings`) - Mock data
6. **Chat Interface** (`/chat`) - Mock chat implementation

### Existing Backend Integration
- Authentication (JWT): ✅ Working
- User profile: ✅ Working
- Dashboard health: ✅ Working
- API client structure: ✅ Established

### Phase 2 Backend Endpoints Available
- `/api/phase2/memory/*` - Memory management
- `/api/phase2/prompts/*` - Prompt system
- `/api/phase2/users/{user_id}/profile` - User profiles with roles
- `/api/phase2/health` - System health
- `/api/phase2/stats` - Memory statistics

---

## Integration Strategy

### Phase A: API Client Enhancement
**Goal**: Extend `api-client.ts` with Phase 2 endpoints

#### New TypeScript Interfaces

```typescript
// Phase 2 User Profile (extended)
export interface Phase2UserProfile extends UserProfile {
  role: 'parent' | 'teenager' | 'child' | 'grandparent' | 'member';
  language_preference: 'en' | 'es';
  age_group?: string;
  parental_controls?: ParentalControls;
}

// Memory Types
export interface MemorySearchRequest {
  query: string;
  user_id: string;
  limit?: number;
  context_window?: number;
}

export interface MemorySearchResult {
  results: Memory[];
  total: number;
  sources: string[];
}

export interface Memory {
  id: string;
  content: string;
  metadata: Record<string, any>;
  timestamp: string;
  source: 'redis' | 'mem0' | 'postgres' | 'qdrant' | 'archive';
  relevance_score?: number;
}

// Prompt Types
export interface PromptBuildRequest {
  user_id: string;
  conversation_id: string;
  minimal?: boolean;
}

export interface PromptResponse {
  system_prompt: string;
  context: string;
  metadata: {
    role: string;
    language: string;
    layers: string[];
  };
}

// Family Member Management
export interface FamilyMember {
  id: string;
  name: string;
  email: string;
  role: 'parent' | 'teenager' | 'child' | 'grandparent';
  avatar?: string;
  language_preference: 'en' | 'es';
  parental_controls?: ParentalControls;
  created_at: string;
  last_active?: string;
}

export interface ParentalControls {
  safe_search: boolean;
  content_filter: 'strict' | 'moderate' | 'off';
  screen_time_daily: number;
  screen_time_weekend: number;
  allowed_apps: string[];
  blocked_keywords: string[];
}

// Knowledge Base
export interface KnowledgeItem {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  contributors: string[];
  created_at: string;
  updated_at: string;
}

// Activity Reports
export interface ActivityReport {
  user_id: string;
  user_name: string;
  date: string;
  queries: number;
  screen_time_hours: number;
  topics: string[];
  sentiment?: 'positive' | 'neutral' | 'negative';
}

// System Health
export interface Phase2Health {
  status: 'healthy' | 'degraded' | 'unhealthy';
  redis: { connected: boolean; latency_ms: number };
  mem0: { connected: boolean; status: string };
  qdrant: { connected: boolean; collections: number };
  ollama: { connected: boolean; models: string[] };
  timestamp: string;
}

// System Statistics
export interface SystemStats {
  total_memories: number;
  memories_by_layer: Record<string, number>;
  total_users: number;
  active_conversations: number;
  storage_usage_mb: number;
  cache_hit_rate: number;
}
```

#### New API Client Methods

```typescript
class ApiClient {
  // ... existing methods ...

  // ============================================================================
  // Phase 2: Memory Management
  // ============================================================================

  async searchMemories(request: MemorySearchRequest): Promise<MemorySearchResult> {
    return this.request<MemorySearchResult>('/api/phase2/memory/search', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async saveContext(conversationId: string, context: string): Promise<void> {
    return this.request<void>('/api/phase2/memory/save', {
      method: 'POST',
      body: JSON.stringify({ conversation_id: conversationId, context }),
    });
  }

  async getConversationContext(conversationId: string): Promise<Memory[]> {
    return this.request<Memory[]>(`/api/phase2/memory/context/${conversationId}`);
  }

  // ============================================================================
  // Phase 2: Prompt System
  // ============================================================================

  async buildPrompt(request: PromptBuildRequest): Promise<PromptResponse> {
    return this.request<PromptResponse>('/api/phase2/prompts/build', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getRolePrompt(role: string): Promise<{ prompt: string }> {
    return this.request<{ prompt: string }>(`/api/phase2/prompts/role/${role}`);
  }

  async getCorePrompt(): Promise<{ prompt: string }> {
    return this.request<{ prompt: string }>('/api/phase2/prompts/core');
  }

  // ============================================================================
  // Phase 2: User Management
  // ============================================================================

  async getPhase2UserProfile(userId: string): Promise<Phase2UserProfile> {
    return this.request<Phase2UserProfile>(`/api/phase2/users/${userId}/profile`);
  }

  async updateUserProfile(userId: string, profile: Partial<Phase2UserProfile>): Promise<Phase2UserProfile> {
    return this.request<Phase2UserProfile>(`/api/phase2/users/${userId}/profile`, {
      method: 'PUT',
      body: JSON.stringify(profile),
    });
  }

  // ============================================================================
  // Family Management
  // ============================================================================

  async getFamilyMembers(): Promise<FamilyMember[]> {
    // TODO: Backend endpoint needed
    return this.request<FamilyMember[]>('/api/family/members');
  }

  async createFamilyMember(member: Partial<FamilyMember>): Promise<FamilyMember> {
    return this.request<FamilyMember>('/api/family/members', {
      method: 'POST',
      body: JSON.stringify(member),
    });
  }

  async updateFamilyMember(memberId: string, updates: Partial<FamilyMember>): Promise<FamilyMember> {
    return this.request<FamilyMember>(`/api/family/members/${memberId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async getParentalControls(memberId: string): Promise<ParentalControls> {
    return this.request<ParentalControls>(`/api/family/members/${memberId}/controls`);
  }

  async updateParentalControls(memberId: string, controls: ParentalControls): Promise<void> {
    return this.request<void>(`/api/family/members/${memberId}/controls`, {
      method: 'PUT',
      body: JSON.stringify(controls),
    });
  }

  // ============================================================================
  // Knowledge Base
  // ============================================================================

  async getKnowledgeItems(category?: string): Promise<KnowledgeItem[]> {
    const params = category ? `?category=${category}` : '';
    return this.request<KnowledgeItem[]>(`/api/knowledge${params}`);
  }

  async createKnowledgeItem(item: Partial<KnowledgeItem>): Promise<KnowledgeItem> {
    return this.request<KnowledgeItem>('/api/knowledge', {
      method: 'POST',
      body: JSON.stringify(item),
    });
  }

  async updateKnowledgeItem(itemId: string, updates: Partial<KnowledgeItem>): Promise<KnowledgeItem> {
    return this.request<KnowledgeItem>(`/api/knowledge/${itemId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  // ============================================================================
  // Activity Reports
  // ============================================================================

  async getActivityReports(startDate?: string, endDate?: string): Promise<ActivityReport[]> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    return this.request<ActivityReport[]>(`/api/reports/activity?${params}`);
  }

  // ============================================================================
  // System Health & Stats
  // ============================================================================

  async getPhase2Health(): Promise<Phase2Health> {
    return this.request<Phase2Health>('/api/phase2/health');
  }

  async getSystemStats(): Promise<SystemStats> {
    return this.request<SystemStats>('/api/phase2/stats');
  }

  // ============================================================================
  // Chat Integration
  // ============================================================================

  async sendChatMessage(message: string, conversationId: string): Promise<{ response: string }> {
    return this.request<{ response: string }>('/api/chat/send', {
      method: 'POST',
      body: JSON.stringify({ message, conversation_id: conversationId }),
    });
  }

  async getChatHistory(conversationId: string): Promise<Array<{ role: string; content: string }>> {
    return this.request<Array<{ role: string; content: string }>>(
      `/api/chat/history/${conversationId}`
    );
  }
}
```

---

### Phase B: Page Integration (Priority Order)

#### 1. Dashboard Enhancement (High Priority) ✅ Partially Done
**Current**: Basic health check
**Enhancement**: Add Phase 2 system health and stats

```typescript
// Update src/app/(admin)/page.tsx
const [phase2Health, setPhase2Health] = useState<Phase2Health | null>(null);
const [systemStats, setSystemStats] = useState<SystemStats | null>(null);

useEffect(() => {
  const fetchData = async () => {
    const [health, stats] = await Promise.all([
      apiClient.getPhase2Health(),
      apiClient.getSystemStats(),
    ]);
    setPhase2Health(health);
    setSystemStats(stats);
  };
  fetchData();
}, []);
```

**New Dashboard Cards**:
- Memory System Status (5 layers)
- Active Users Count
- Recent Activity Summary
- Storage Usage

---

#### 2. MyFamily Page Integration (High Priority)
**Tabs to Integrate**:
1. **Family Members Tab**:
   - Fetch: `apiClient.getFamilyMembers()`
   - Create: `apiClient.createFamilyMember()`
   - Update: `apiClient.updateFamilyMember()`

2. **Parental Controls Tab**:
   - Fetch: `apiClient.getParentalControls(memberId)`
   - Update: `apiClient.updateParentalControls(memberId, controls)`

3. **Feature Flags Tab**:
   - Backend endpoint needed: `/api/features/flags`
   - Or store in user profile metadata

4. **Activity Reports Tab**:
   - Fetch: `apiClient.getActivityReports()`
   - Filter by date range and user

**Implementation Steps**:
1. Create `src/hooks/useFamilyMembers.ts` custom hook
2. Replace mock data with API calls
3. Add loading states and error handling
4. Implement form validation for updates

---

#### 3. Chat Interface Integration (High Priority)
**Backend Connection**:
- Use Phase 2 prompt building: `apiClient.buildPrompt()`
- Send messages: `apiClient.sendChatMessage()`
- Fetch history: `apiClient.getChatHistory()`
- Save context: `apiClient.saveContext()`

**Features to Implement**:
1. Real-time message streaming (if backend supports)
2. Conversation context loading
3. Role-based prompt selection
4. Message persistence

**Implementation Steps**:
1. Create `src/hooks/useChat.ts` custom hook
2. Integrate with Phase 2 prompt system
3. Add conversation history persistence
4. Implement typing indicators and message status

---

#### 4. Family Shared Knowledge (Medium Priority)
**Backend Endpoints Needed**:
- `GET /api/knowledge` - List items
- `POST /api/knowledge` - Create item
- `PUT /api/knowledge/{id}` - Update item
- `DELETE /api/knowledge/{id}` - Delete item

**Integration**:
- Category filtering
- Tag-based search
- Contributor tracking
- Version history (future)

---

#### 5. MCP & Tools Integration (Medium Priority)
**Real Tool Status**:
- Memory Store (Mem0): Connected via Phase 2 health
- LLM Inference: Via Phase 2 health (Ollama)
- Vector DB: Via Phase 2 health (Qdrant)
- Redis: Via Phase 2 health

**Implementation**:
1. Replace mock data with `apiClient.getPhase2Health()`
2. Parse health response to show individual service status
3. Add real-time status updates (polling or WebSocket)
4. Add service configuration UI

---

#### 6. General Settings (Low Priority)
**Settings to Backend**:
- User preferences → `/api/phase2/users/{id}/profile`
- System config → New endpoint needed: `/api/system/config`
- Theme settings → Store in user profile or localStorage

---

### Phase C: Real-time Features

#### WebSocket Integration (Optional)
For real-time updates in Chat and Dashboard:

```typescript
// src/lib/websocket-client.ts
class WebSocketClient {
  private ws: WebSocket | null = null;

  connect(token: string) {
    this.ws = new WebSocket(`ws://100.81.76.55:30080/ws?token=${token}`);

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Handle different message types
      switch (data.type) {
        case 'chat_message':
          // Update chat UI
          break;
        case 'system_health':
          // Update dashboard
          break;
        case 'memory_update':
          // Refresh memory UI
          break;
      }
    };
  }

  sendMessage(message: any) {
    this.ws?.send(JSON.stringify(message));
  }

  disconnect() {
    this.ws?.close();
  }
}
```

---

### Phase D: Backend Endpoints to Create

#### Missing Endpoints Needed:
1. **Family Management**:
   - `GET /api/family/members` - List family members
   - `POST /api/family/members` - Create member
   - `PUT /api/family/members/{id}` - Update member
   - `DELETE /api/family/members/{id}` - Delete member
   - `GET /api/family/members/{id}/controls` - Get controls
   - `PUT /api/family/members/{id}/controls` - Update controls

2. **Knowledge Base**:
   - `GET /api/knowledge` - List items
   - `POST /api/knowledge` - Create item
   - `PUT /api/knowledge/{id}` - Update item
   - `DELETE /api/knowledge/{id}` - Delete item
   - `GET /api/knowledge/search` - Search knowledge

3. **Activity Reports**:
   - `GET /api/reports/activity` - Get activity reports
   - `GET /api/reports/usage` - Get usage statistics
   - `GET /api/reports/export` - Export reports

4. **Chat**:
   - `POST /api/chat/send` - Send message (integrate with Phase 2 prompts)
   - `GET /api/chat/history/{conversation_id}` - Get conversation
   - `DELETE /api/chat/history/{conversation_id}` - Clear conversation
   - `WS /ws` - WebSocket for real-time chat (optional)

5. **System Configuration**:
   - `GET /api/system/config` - Get system settings
   - `PUT /api/system/config` - Update system settings
   - `GET /api/system/features` - Get feature flags
   - `PUT /api/system/features` - Update feature flags

---

## Implementation Timeline

### Week 1: Foundation
- [ ] Extend `api-client.ts` with TypeScript interfaces
- [ ] Add Phase 2 API methods to ApiClient class
- [ ] Test all Phase 2 endpoints with curl
- [ ] Update Dashboard with Phase 2 health and stats

### Week 2: Core Features
- [ ] Integrate MyFamily page (Members and Controls tabs)
- [ ] Create custom hooks for data fetching
- [ ] Add loading states and error boundaries
- [ ] Implement form validation

### Week 3: Chat & Knowledge
- [ ] Integrate Chat interface with Phase 2 prompts
- [ ] Add conversation persistence
- [ ] Integrate Family Shared Knowledge page
- [ ] Add MCP & Tools real-time status

### Week 4: Backend Expansion
- [ ] Create missing backend endpoints (Family, Knowledge, Reports)
- [ ] Add WebSocket support for real-time updates
- [ ] Implement Activity Reports backend
- [ ] Add system configuration endpoints

### Week 5: Polish & Testing
- [ ] End-to-end testing all pages
- [ ] Add optimistic UI updates
- [ ] Implement caching strategies
- [ ] Performance optimization

---

## Testing Strategy

### Unit Tests
- Test API client methods
- Test custom hooks with mock data
- Test components in isolation

### Integration Tests
- Test full user flows (login → navigate → action)
- Test error handling and recovery
- Test real-time updates

### E2E Tests
- Use Playwright for full application testing
- Test across different roles (parent, child, etc.)
- Test mobile responsiveness

---

## Security Considerations

1. **Authentication**: JWT tokens with refresh mechanism
2. **Role-Based Access**: Enforce permissions on frontend and backend
3. **Data Validation**: Validate all user inputs before API calls
4. **XSS Protection**: Sanitize user-generated content in Knowledge Base and Chat
5. **CSRF Protection**: Use proper CORS configuration
6. **Sensitive Data**: Don't expose tokens or sensitive info in logs

---

## Performance Optimization

1. **React Query / SWR**: Use for data fetching and caching
2. **Optimistic Updates**: Update UI before backend confirmation
3. **Pagination**: Implement for long lists (Knowledge, Chat history)
4. **Lazy Loading**: Load components and data on-demand
5. **Image Optimization**: Use Next.js Image component
6. **Code Splitting**: Split bundle by routes

---

## Next Steps

1. **Immediate**: Extend `api-client.ts` with Phase 2 methods
2. **Priority 1**: Integrate MyFamily page with backend
3. **Priority 2**: Connect Chat interface to Phase 2 prompts
4. **Priority 3**: Create missing backend endpoints
5. **Future**: Add WebSocket support for real-time features

---

## Questions & Decisions Needed

1. **WebSocket vs Polling**: Do we need real-time updates or is polling sufficient?
2. **Feature Flags Storage**: Store in database or configuration file?
3. **Knowledge Base Storage**: Use Phase 2 memory system or separate table?
4. **Chat Persistence**: How long to keep conversation history?
5. **Activity Reports**: What metrics to track and how granular?

---

## Appendix: Example Usage

### MyFamily Page Integration Example

```typescript
// src/app/(admin)/family/page.tsx
"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api-client";
import type { FamilyMember } from "@/lib/api-client";

export default function MyFamily() {
  const [members, setMembers] = useState<FamilyMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMembers = async () => {
      try {
        const data = await apiClient.getFamilyMembers();
        setMembers(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    };
    fetchMembers();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      {members.map((member) => (
        <MemberCard key={member.id} member={member} />
      ))}
    </div>
  );
}
```
