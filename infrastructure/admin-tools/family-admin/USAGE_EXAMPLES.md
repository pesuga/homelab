# API Routes Usage Examples

## React Component Examples

### Example 1: Chat Component

```typescript
'use client';

import { useState } from 'react';
import { apiPost } from '@/types/api';
import type { ChatRequest, ChatResponse } from '@/types/api';

export function ChatComponent() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    setLoading(true);
    try {
      // ✅ Correct: Use API route (server-side proxy)
      const result = await apiPost<ChatResponse>('/api/family/chat', {
        message,
        userId: 'user-123',
      } as ChatRequest);

      setResponse(result.response);
    } catch (error) {
      console.error('Chat error:', error);
      alert('Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type a message..."
      />
      <button onClick={sendMessage} disabled={loading}>
        {loading ? 'Sending...' : 'Send'}
      </button>
      {response && <p>Response: {response}</p>}
    </div>
  );
}
```

### Example 2: Family Members List

```typescript
'use client';

import { useEffect, useState } from 'react';
import { apiGet, apiPost, apiDelete } from '@/types/api';
import type { FamilyMember, CreateFamilyMemberRequest } from '@/types/api';

export function FamilyMembersList() {
  const [members, setMembers] = useState<FamilyMember[]>([]);
  const [loading, setLoading] = useState(true);

  // Load members on mount
  useEffect(() => {
    loadMembers();
  }, []);

  const loadMembers = async () => {
    try {
      const response = await apiGet<{ members: FamilyMember[] }>('/api/family/members');
      setMembers(response.members);
    } catch (error) {
      console.error('Failed to load members:', error);
    } finally {
      setLoading(false);
    }
  };

  const addMember = async (data: CreateFamilyMemberRequest) => {
    try {
      await apiPost('/api/family/members', data);
      await loadMembers(); // Reload list
    } catch (error) {
      console.error('Failed to add member:', error);
    }
  };

  const removeMember = async (id: string) => {
    try {
      await apiDelete(`/api/family/members?id=${id}`);
      await loadMembers(); // Reload list
    } catch (error) {
      console.error('Failed to remove member:', error);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h2>Family Members</h2>
      <ul>
        {members.map((member) => (
          <li key={member.id}>
            {member.name} ({member.role})
            <button onClick={() => removeMember(member.id)}>Remove</button>
          </li>
        ))}
      </ul>
      <button onClick={() => addMember({
        name: 'New Member',
        role: 'child',
        age: 10
      })}>
        Add Member
      </button>
    </div>
  );
}
```

### Example 3: Health Check Component

```typescript
'use client';

import { useEffect, useState } from 'react';
import { apiGet } from '@/types/api';
import type { HealthResponse } from '@/types/api';

export function HealthStatus() {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const status = await apiGet<HealthResponse>('/api/health');
        setHealth(status);
      } catch (error) {
        console.error('Health check failed:', error);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30s

    return () => clearInterval(interval);
  }, []);

  if (!health) return <div>Checking status...</div>;

  return (
    <div>
      <h3>System Status: {health.status}</h3>
      <ul>
        {Object.entries(health.services).map(([name, service]) => (
          <li key={name}>
            {name}: {service.healthy ? '✅' : '❌'} {service.message}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

### Example 4: Direct LLM Access

```typescript
'use client';

import { useState } from 'react';
import { apiPost } from '@/types/api';
import type { LLMChatRequest, LLMChatResponse } from '@/types/api';

export function DirectLLMChat() {
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const sendToLLM = async () => {
    setLoading(true);
    try {
      const result = await apiPost<LLMChatResponse>('/api/llm/chat', {
        message: prompt,
        temperature: 0.7,
        max_tokens: 512,
        system_prompt: 'You are a helpful family assistant.',
      } as LLMChatRequest);

      setResponse(result.response);
      console.log('Token usage:', result.usage);
    } catch (error) {
      console.error('LLM error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Ask anything..."
      />
      <button onClick={sendToLLM} disabled={loading}>
        Send to LLM
      </button>
      {response && <pre>{response}</pre>}
    </div>
  );
}
```

## Server Component Examples

### Example 5: Server-Side Data Fetching

```typescript
// app/dashboard/page.tsx
import { API_CONFIG } from '@/lib/api-helpers';
import type { FamilyMember } from '@/types/api';

export default async function DashboardPage() {
  // Server components can directly access internal services
  const response = await fetch(`${API_CONFIG.familyApi}/api/family/members`);
  const data = await response.json();
  const members: FamilyMember[] = data.members;

  return (
    <div>
      <h1>Family Dashboard</h1>
      <ul>
        {members.map((member) => (
          <li key={member.id}>{member.name}</li>
        ))}
      </ul>
    </div>
  );
}
```

## Error Handling Patterns

### Pattern 1: Try-Catch with User Feedback

```typescript
const handleAction = async () => {
  try {
    const result = await apiPost('/api/family/chat', { message: 'Hello' });
    // Success
    setData(result);
  } catch (error) {
    // Error handling
    if (error instanceof Error) {
      alert(`Error: ${error.message}`);
    } else {
      alert('An unexpected error occurred');
    }
  }
};
```

### Pattern 2: Error State Management

```typescript
const [error, setError] = useState<string | null>(null);

const fetchData = async () => {
  setError(null);
  try {
    const result = await apiGet('/api/family/members');
    setMembers(result.members);
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Failed to load data');
  }
};

return (
  <div>
    {error && <div className="error">{error}</div>}
    {/* ... rest of component */}
  </div>
);
```

### Pattern 3: Toast Notifications

```typescript
import { toast } from 'react-toastify'; // or your toast library

const saveData = async () => {
  try {
    await apiPost('/api/family/members', newMember);
    toast.success('Member added successfully!');
  } catch (error) {
    toast.error('Failed to add member');
    console.error(error);
  }
};
```

## Custom Hooks

### useApiQuery Hook

```typescript
// hooks/useApiQuery.ts
import { useState, useEffect } from 'react';
import { apiGet } from '@/types/api';

export function useApiQuery<T>(endpoint: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await apiGet<T>(endpoint);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [endpoint]);

  return { data, loading, error, refetch: () => setLoading(true) };
}

// Usage:
const { data, loading, error } = useApiQuery<HealthResponse>('/api/health');
```

### useApiMutation Hook

```typescript
// hooks/useApiMutation.ts
import { useState } from 'react';
import { apiPost } from '@/types/api';

export function useApiMutation<TRequest, TResponse>(endpoint: string) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const mutate = async (data: TRequest): Promise<TResponse | null> => {
    setLoading(true);
    setError(null);

    try {
      const result = await apiPost<TResponse>(endpoint, data);
      return result;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { mutate, loading, error };
}

// Usage:
const { mutate, loading } = useApiMutation<ChatRequest, ChatResponse>('/api/family/chat');
const result = await mutate({ message: 'Hello' });
```

## Testing Examples

### Test API Route Handler

```typescript
// __tests__/api/health.test.ts
import { GET } from '@/app/api/health/route';

describe('/api/health', () => {
  it('returns health status', async () => {
    const response = await GET();
    const data = await response.json();

    expect(data.status).toBe('ok');
    expect(data.services).toBeDefined();
  });
});
```

### Test React Component with API

```typescript
// __tests__/components/ChatComponent.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChatComponent } from '@/components/ChatComponent';

// Mock API
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ response: 'Hello back!' }),
  })
) as jest.Mock;

test('sends chat message', async () => {
  render(<ChatComponent />);

  const input = screen.getByPlaceholderText('Type a message...');
  const button = screen.getByText('Send');

  fireEvent.change(input, { target: { value: 'Hello' } });
  fireEvent.click(button);

  await waitFor(() => {
    expect(screen.getByText(/Hello back!/)).toBeInTheDocument();
  });
});
```

## Common Mistakes to Avoid

### ❌ Wrong: Using Internal URLs in Browser

```typescript
// This will fail - browser can't resolve cluster DNS
const response = await fetch('http://family-assistant-backend.homelab:8001/api/chat');
```

### ✅ Correct: Using API Routes

```typescript
// This works - proxied through Next.js API route
const response = await fetch('/api/family/chat');
```

### ❌ Wrong: Accessing Environment Variables in Browser

```typescript
// This is undefined in browser (not prefixed with NEXT_PUBLIC_)
const apiUrl = process.env.FAMILY_API_URL;
```

### ✅ Correct: Environment Variables

```typescript
// In API route (server-side)
const apiUrl = process.env.FAMILY_API_URL; // ✅ Works

// In browser component
const apiUrl = '/api/family'; // ✅ Use relative paths
```

### ❌ Wrong: Not Handling Errors

```typescript
const data = await fetch('/api/family/members').then(r => r.json());
// No error handling!
```

### ✅ Correct: Proper Error Handling

```typescript
try {
  const response = await fetch('/api/family/members');
  if (!response.ok) throw new Error('Request failed');
  const data = await response.json();
} catch (error) {
  console.error('Error:', error);
  // Handle error appropriately
}
```
