/**
 * LobeChat mem0 Middleware
 *
 * Purpose: Bridge between LobeChat and Ollama with mem0 memory injection
 *
 * Flow:
 * 1. LobeChat sends chat request to this middleware
 * 2. Middleware fetches relevant memories from mem0
 * 3. Injects memories into system prompt
 * 4. Forwards enhanced request to Ollama
 * 5. Returns Ollama response to LobeChat
 * 6. Asynchronously stores new memories to mem0
 */

const express = require('express');
const axios = require('axios');
const app = express();

// Configuration
const PORT = process.env.PORT || 11435;  // One port above Ollama
const OLLAMA_URL = process.env.OLLAMA_URL || 'http://100.72.98.106:11434';
const MEM0_URL = process.env.MEM0_URL || 'http://mem0.homelab.svc.cluster.local:8080';

app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'lobechat-mem0-middleware' });
});

// Proxy Ollama API endpoints (non-chat)
app.get('/api/*', async (req, res) => {
  try {
    const response = await axios({
      method: req.method,
      url: `${OLLAMA_URL}${req.path}`,
      headers: { 'Content-Type': 'application/json' },
    });
    res.json(response.data);
  } catch (error) {
    console.error('Proxy error:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// Main chat endpoint with mem0 integration
app.post('/api/chat', async (req, res) => {
  try {
    const { model, messages, stream = false, options = {} } = req.body;

    // Extract user ID from request (or use default)
    const userId = req.headers['x-user-id'] || 'default_user';

    // Get conversation context (last user message)
    const userMessages = messages.filter(m => m.role === 'user');
    const lastUserMessage = userMessages[userMessages.length - 1]?.content || '';

    console.log(`[mem0] Fetching memories for user: ${userId}`);
    console.log(`[mem0] Query context: ${lastUserMessage.substring(0, 100)}...`);

    // Fetch relevant memories from mem0
    let memories = [];
    try {
      const memoryResponse = await axios.post(
        `${MEM0_URL}/v1/memories/search/`,
        {
          query: lastUserMessage,
          user_id: userId,
          limit: 5  // Top 5 relevant memories
        },
        { timeout: 3000 }
      );

      if (memoryResponse.data && memoryResponse.data.results) {
        memories = memoryResponse.data.results.map(m => m.memory);
        console.log(`[mem0] Retrieved ${memories.length} memories`);
      }
    } catch (memError) {
      console.warn('[mem0] Memory fetch failed:', memError.message);
      // Continue without memories if mem0 is unavailable
    }

    // Build enhanced system prompt with memories
    let systemPrompt = messages.find(m => m.role === 'system')?.content ||
      'You are a helpful AI assistant.';

    if (memories.length > 0) {
      const memoryContext = `

RELEVANT MEMORIES ABOUT USER:
${memories.map((m, i) => `${i + 1}. ${m}`).join('\n')}

Use these memories to provide personalized, context-aware responses.`;

      systemPrompt += memoryContext;
      console.log(`[mem0] Injected ${memories.length} memories into context`);
    }

    // Replace or add enhanced system message
    const enhancedMessages = messages.filter(m => m.role !== 'system');
    enhancedMessages.unshift({ role: 'system', content: systemPrompt });

    // Forward to Ollama
    console.log(`[ollama] Forwarding to model: ${model}`);
    const ollamaResponse = await axios.post(
      `${OLLAMA_URL}/api/chat`,
      {
        model,
        messages: enhancedMessages,
        stream,
        options
      },
      {
        responseType: stream ? 'stream' : 'json',
        timeout: 120000  // 2 minute timeout for generation
      }
    );

    if (stream) {
      // Stream response back to client
      res.setHeader('Content-Type', 'application/x-ndjson');
      ollamaResponse.data.pipe(res);
    } else {
      // Send JSON response
      const response = ollamaResponse.data;
      res.json(response);

      // Asynchronously store new memories (don't wait)
      storeMemories(userId, lastUserMessage, response.message?.content);
    }

  } catch (error) {
    console.error('[error] Chat endpoint failed:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// Async function to store memories
async function storeMemories(userId, userMessage, assistantResponse) {
  try {
    // Build conversation context for mem0
    const messages = [
      { role: 'user', content: userMessage }
    ];

    if (assistantResponse) {
      messages.push({ role: 'assistant', content: assistantResponse });
    }

    // Send to mem0 for memory extraction
    await axios.post(
      `${MEM0_URL}/v1/memories/`,
      {
        messages,
        user_id: userId
      },
      { timeout: 5000 }
    );

    console.log(`[mem0] Stored memories for user: ${userId}`);
  } catch (error) {
    console.warn('[mem0] Memory storage failed:', error.message);
    // Non-critical, don't throw
  }
}

// Proxy other Ollama endpoints
app.post('/api/generate', async (req, res) => {
  try {
    const response = await axios.post(
      `${OLLAMA_URL}/api/generate`,
      req.body,
      { responseType: req.body.stream ? 'stream' : 'json' }
    );

    if (req.body.stream) {
      res.setHeader('Content-Type', 'application/x-ndjson');
      response.data.pipe(res);
    } else {
      res.json(response.data);
    }
  } catch (error) {
    console.error('Generate error:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`[middleware] LobeChat mem0 Middleware listening on port ${PORT}`);
  console.log(`[middleware] Proxying to Ollama: ${OLLAMA_URL}`);
  console.log(`[middleware] mem0 Memory API: ${MEM0_URL}`);
});
