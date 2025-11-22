const CACHE_NAME = 'nexus-family-assistant-v1';
const API_CACHE_NAME = 'nexus-api-v1';

// Assets to cache for offline functionality
const STATIC_ASSETS = [
  '/',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
  // Add other static assets as needed
];

// API endpoints to cache for offline functionality
const API_ENDPOINTS = [
  '/api/dashboard/health',
  '/api/family/members',
  '/api/family/activities',
  '/api/user/profile'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('Service Worker: Static assets cached');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('Service Worker: Failed to cache static assets', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
              console.log('Service Worker: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker: Activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - handle requests with offline support
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
  }
  // Handle static asset requests
  else {
    event.respondWith(handleStaticRequest(request));
  }
});

// Handle API requests with network-first strategy
async function handleApiRequest(request) {
  const url = new URL(request.url);

  try {
    // Try network first for API requests
    const networkResponse = await fetch(request);

    // Cache successful GET requests
    if (request.method === 'GET' && networkResponse.ok) {
      const cache = await caches.open(API_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('Service Worker: Network failed for API request, trying cache', request.url);

    // Fallback to cache for GET requests
    if (request.method === 'GET') {
      const cachedResponse = await caches.match(request);
      if (cachedResponse) {
        return cachedResponse;
      }
    }

    // Return offline response for critical API endpoints
    if (API_ENDPOINTS.some(endpoint => url.pathname === endpoint)) {
      return new Response(JSON.stringify({
        error: 'Offline',
        message: 'No network connection. Showing cached data.',
        timestamp: new Date().toISOString(),
        offline: true
      }), {
        status: 503,
        statusText: 'Service Unavailable',
        headers: {
          'Content-Type': 'application/json'
        }
      });
    }

    throw error;
  }
}

// Handle static requests with cache-first strategy
async function handleStaticRequest(request) {
  try {
    // Try cache first for static assets
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // Fallback to network
    const networkResponse = await fetch(request);

    // Cache successful responses
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('Service Worker: Network failed for static request', request.url);

    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return caches.match('/') || new Response(`
        <!DOCTYPE html>
        <html>
          <head>
            <title>Offline - Nexus Family Assistant</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
              body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin: 0;
                padding: 2rem;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                text-align: center;
              }
              .offline-icon {
                width: 80px;
                height: 80px;
                margin-bottom: 1rem;
                opacity: 0.8;
              }
              h1 {
                margin: 0 0 1rem 0;
                font-size: 2rem;
                font-weight: 600;
              }
              p {
                margin: 0 0 2rem 0;
                opacity: 0.9;
                max-width: 400px;
                line-height: 1.5;
              }
              .retry-btn {
                background: white;
                color: #667eea;
                border: none;
                padding: 0.75rem 2rem;
                border-radius: 50px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
              }
              .retry-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(0,0,0,0.2);
              }
            </style>
          </head>
          <body>
            <svg class="offline-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path>
              <line x1="12" y1="2" x2="12" y2="12"></line>
              <line x1="12" y1="22" x2="12" y2="18"></line>
            </svg>
            <h1>You're Offline</h1>
            <p>Nexus Family Assistant is not connected to the internet. Some features may be limited until you're back online.</p>
            <button class="retry-btn" onclick="window.location.reload()">
              Try Again
            </button>
          </body>
        </html>
      `, {
        status: 200,
        statusText: 'OK',
        headers: {
          'Content-Type': 'text/html'
        }
      });
    }

    throw error;
  }
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

async function doBackgroundSync() {
  try {
    // Sync any pending offline actions
    console.log('Service Worker: Performing background sync');

    // Get all pending offline actions from IndexedDB
    const pendingActions = await getPendingOfflineActions();

    // Process each action
    for (const action of pendingActions) {
      try {
        await fetch(action.url, {
          method: action.method,
          headers: action.headers,
          body: action.body
        });

        // Remove successful action from pending queue
        await removePendingOfflineAction(action.id);
      } catch (error) {
        console.error('Service Worker: Failed to sync action', action, error);
      }
    }
  } catch (error) {
    console.error('Service Worker: Background sync failed', error);
  }
}

// Push notification handling
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();

    const options = {
      body: data.body,
      icon: '/icons/icon-192x192.png',
      badge: '/icons/badge-72x72.png',
      vibrate: [100, 50, 100],
      data: data.data,
      actions: data.actions || [
        {
          action: 'open',
          title: 'Open Nexus'
        },
        {
          action: 'dismiss',
          title: 'Dismiss'
        }
      ],
      silent: data.silent || false,
      requireInteraction: data.requireInteraction || false,
      timestamp: Date.now()
    };

    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'open' || !event.action) {
    event.waitUntil(
      clients.openWindow(event.notification.data?.url || '/')
    );
  }
});

// IndexedDB helpers for offline actions
async function getPendingOfflineActions() {
  // This would typically use IndexedDB to store pending actions
  // For now, return empty array
  return [];
}

async function removePendingOfflineAction(actionId) {
  // Remove action from IndexedDB
  console.log('Service Worker: Removing completed offline action', actionId);
}

// Periodic background sync for fresh data
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'refresh-data') {
    event.waitUntil(refreshCachedData());
  }
});

async function refreshCachedData() {
  try {
    console.log('Service Worker: Refreshing cached data');

    // Refresh critical API endpoints
    for (const endpoint of API_ENDPOINTS) {
      try {
        const response = await fetch(endpoint);
        if (response.ok) {
          const cache = await caches.open(API_CACHE_NAME);
          await cache.put(endpoint, response);
        }
      } catch (error) {
        console.log('Service Worker: Failed to refresh endpoint', endpoint, error);
      }
    }
  } catch (error) {
    console.error('Service Worker: Failed to refresh cached data', error);
  }
}