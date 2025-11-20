# Family Assistant Chat Interface - Implementation Guide

## Overview

This document describes the implementation of the chat interface for the Family Assistant app. The chat interface provides a clean, family-friendly way to interact with the Family Assistant AI through text messages.

## Architecture

### Components

1. **ChatInterface** (`src/components/ChatInterface.tsx`)
   - Main container component
   - Manages chat state and message history
   - Handles API communication
   - Provides session management
   - Features:
     - Welcome message on load
     - Auto-scroll to latest messages
     - Clear chat history
     - Retry failed messages
     - Navigate back to home

2. **ChatMessage** (`src/components/ChatMessage.tsx`)
   - Individual message bubble component
   - Displays user and assistant messages
   - Shows timestamps and status indicators
   - Responsive design with proper styling
   - Features:
     - Different styling for user vs assistant
     - Error state visualization
     - Loading/sending state
     - Accessible markup

3. **ChatInput** (`src/components/ChatInput.tsx`)
   - Message input component
   - Auto-resizing textarea
   - Keyboard shortcuts
   - Features:
     - Enter to send, Shift+Enter for new line
     - Auto-resize up to max height
     - Character counter
     - Disabled state during sending
     - Loading spinner

### API Client

**File**: `src/utils/chatApi.ts`

Functions:
- `sendChatMessage(request: ChatRequest)` - Send message to backend
- `generateSessionId()` - Generate unique session ID
- `getOrCreateSessionId()` - Get or create session from localStorage
- `clearSession()` - Clear current session

Features:
- Error handling with custom ChatApiError class
- Session management with localStorage
- Type-safe request/response handling

### Type Definitions

**File**: `src/types/chat.ts`

Types:
- `ChatMessage` - Message object structure
- `ChatRequest` - API request format
- `ChatResponse` - API response format
- `ChatError` - Error response format

## Integration

### Routing

The chat interface is integrated using React Router:

```tsx
// In App.tsx
<Routes>
  <Route path="/" element={<HomeScreen ... />} />
  <Route path="/chat" element={<ChatPage currentUser={currentUser} />} />
</Routes>
```

### Navigation

The chat is accessible from the home screen via:
- Quick Actions grid (first button)
- Direct navigation to `/chat` route

## Configuration

### Environment Variables

Create a `.env.development` or `.env.production` file:

```bash
VITE_API_BASE_URL=http://family-assistant-backend.homelab.svc.cluster.local:8001
```

For local development:
```bash
VITE_API_BASE_URL=http://localhost:8001
```

### Backend API Endpoints

The chat interface connects to:
- `POST /chat` - Main chat endpoint

Expected request format:
```typescript
{
  message: string;
  user_id?: string;
  session_id?: string;
  content_type?: 'text' | 'image' | 'audio' | 'document';
  metadata?: Record<string, any>;
}
```

Expected response format:
```typescript
{
  response: string;
  session_id?: string;
  metadata?: Record<string, any>;
}
```

## Features

### Implemented
- ✅ Text message sending and receiving
- ✅ Message history display
- ✅ Auto-scroll to latest message
- ✅ Loading states
- ✅ Error handling with retry
- ✅ Session management
- ✅ Responsive design
- ✅ Dark mode support
- ✅ Keyboard shortcuts
- ✅ Clear chat history
- ✅ Navigate back to home
- ✅ Timestamps

### Future Enhancements
- 🔜 Voice messages (multimodal)
- 🔜 Image attachments
- 🔜 Document uploads
- 🔜 WebSocket streaming
- 🔜 Authentication
- 🔜 Message persistence
- 🔜 Typing indicators
- 🔜 Read receipts
- 🔜 Message search
- 🔜 Export chat history

## Usage

### For Users

1. **Starting a Chat**
   - Click the "Chat" button from the home screen
   - Welcome message appears automatically

2. **Sending Messages**
   - Type in the input field at bottom
   - Press Enter to send
   - Press Shift+Enter for new line

3. **Clearing History**
   - Click the trash icon in header
   - Confirm the action

4. **Returning Home**
   - Click the home icon in header

### For Developers

#### Running Development Server

```bash
cd apps/family-portal
npm install
npm run dev
```

The app will be available at `http://localhost:3000`

#### Building for Production

```bash
npm run build
```

Output will be in the `dist/` directory.

#### Testing the Chat

1. Ensure backend is running at configured URL
2. Navigate to `/chat`
3. Send a test message
4. Verify response appears
5. Check browser console for errors

## Code Quality

### TypeScript

All components use TypeScript with proper type definitions:
- Props interfaces defined
- State properly typed
- API responses typed
- No `any` types used

### Accessibility

- Semantic HTML structure
- ARIA labels on interactive elements
- Keyboard navigation support
- Screen reader friendly
- High contrast support in dark mode

### Performance

- Auto-scroll debounced
- Messages efficiently rendered
- No unnecessary re-renders
- Optimized bundle size

### Styling

- Tailwind CSS utility classes
- Consistent with app theme
- Responsive breakpoints
- Dark mode support
- Family-friendly colors

## File Structure

```
apps/family-portal/
├── src/
│   ├── components/
│   │   ├── ChatInterface.tsx       # Main chat container
│   │   ├── ChatMessage.tsx         # Message bubble
│   │   └── ChatInput.tsx           # Input field
│   ├── types/
│   │   └── chat.ts                 # Chat type definitions
│   ├── utils/
│   │   └── chatApi.ts              # API client
│   └── App.tsx                     # Routing setup
├── .env.example                    # Environment template
├── .env.development                # Dev configuration
└── CHAT_IMPLEMENTATION.md          # This document
```

## Troubleshooting

### Common Issues

1. **API Connection Fails**
   - Check `VITE_API_BASE_URL` is correct
   - Verify backend is running
   - Check network connectivity
   - Look for CORS errors in console

2. **Messages Not Sending**
   - Check browser console for errors
   - Verify API response format
   - Check session ID in localStorage
   - Test with curl or Postman

3. **Build Errors**
   - Ensure all dependencies installed: `npm install`
   - Check TypeScript errors: `npm run build`
   - Verify vite-env.d.ts exists

4. **Styling Issues**
   - Clear browser cache
   - Check Tailwind configuration
   - Verify dark mode toggle

## API Testing

### Using curl

```bash
# Test the chat endpoint
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, can you help me?",
    "user_id": "1",
    "session_id": "test_session"
  }'
```

Expected response:
```json
{
  "response": "Hello! I'm your Family Assistant. How can I help you today?",
  "session_id": "test_session"
}
```

## Contributing

When adding new features:
1. Update type definitions in `chat.ts`
2. Add tests for new functionality
3. Update this documentation
4. Follow existing code style
5. Ensure accessibility compliance

## License

Same as Family Assistant project.
