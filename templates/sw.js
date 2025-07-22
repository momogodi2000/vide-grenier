// Service Worker pour Vidé-Grenier Kamer PWA
const CACHE_NAME = 'vgk-v1.0.0';
const OFFLINE_URL = '/offline/';

// Ressources à cacher en priorité
const CORE_CACHE_RESOURCES = [
  '/',
  '/static/css/tailwind.min.css',
  '/static/css/custom.css',
  '/static/js/app.js',
  '/static/js/pwa.js',
  '/static/images/icons/icon-192x192.png',
  '/static/images/icons/icon-512x512.png',
  OFFLINE_URL
];

// Ressources à cacher au runtime
const RUNTIME_CACHE_RESOURCES = [
  '/products/',
  '/categories/',
  '/dashboard/',
  '/auth/login/',
  '/auth/register/'
];

// Stratégies de cache
const CACHE_STRATEGIES = {
  'CACHE_FIRST': 'cache-first',
  'NETWORK_FIRST': 'network-first', 
  'CACHE_ONLY': 'cache-only',
  'NETWORK_ONLY': 'network-only',
  'STALE_WHILE_REVALIDATE': 'stale-while-revalidate'
};

// Configuration des routes
const ROUTE_CACHE_CONFIG = {
  // API calls - Network first avec fallback
  '/api/': CACHE_STRATEGIES.NETWORK_FIRST,
  
  // Static assets - Cache first
  '/static/': CACHE_STRATEGIES.CACHE_FIRST,
  
  // Images - Stale while revalidate
  '/media/': CACHE_STRATEGIES.STALE_WHILE_REVALIDATE,
  
  // Pages - Network first pour contenu frais
  '/products/': CACHE_STRATEGIES.NETWORK_FIRST,
  '/dashboard/': CACHE_STRATEGIES.NETWORK_FIRST,
  
  // Auth pages - Network only (données sensibles)
  '/auth/': CACHE_STRATEGIES.NETWORK_ONLY
};

// Installation du Service Worker
self.addEventListener('install', event => {
  console.log('[SW] Installation démarrée');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Cache ouvert:', CACHE_NAME);
        return cache.addAll(CORE_CACHE_RESOURCES);
      })
      .then(() => {
        console.log('[SW] Ressources core cachées');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('[SW] Erreur installation:', error);
      })
  );
});

// Activation du Service Worker
self.addEventListener('activate', event => {
  console.log('[SW] Activation démarrée');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            // Supprimer les anciens caches
            if (cacheName !== CACHE_NAME) {
              console.log('[SW] Suppression ancien cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[SW] Activation terminée');
        return self.clients.claim();
      })
  );
});

// Interception des requêtes
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  
  // Ignorer les requêtes non-HTTP
  if (!request.url.startsWith('http')) {
    return;
  }
  
  // Ignorer les requêtes POST/PUT/DELETE pour les données critiques
  if (request.method !== 'GET') {
    return;
  }
  
  // Déterminer la stratégie de cache
  const strategy = getCacheStrategy(url.pathname);
  
  event.respondWith(
    handleRequest(request, strategy)
  );
});

// Déterminer la stratégie de cache selon l'URL
function getCacheStrategy(pathname) {
  for (const [route, strategy] of Object.entries(ROUTE_CACHE_CONFIG)) {
    if (pathname.startsWith(route)) {
      return strategy;
    }
  }
  
  // Stratégie par défaut
  return CACHE_STRATEGIES.NETWORK_FIRST;
}

// Gestionnaire principal des requêtes
async function handleRequest(request, strategy) {
  switch (strategy) {
    case CACHE_STRATEGIES.CACHE_FIRST:
      return cacheFirst(request);
    
    case CACHE_STRATEGIES.NETWORK_FIRST:
      return networkFirst(request);
    
    case CACHE_STRATEGIES.CACHE_ONLY:
      return cacheOnly(request);
    
    case CACHE_STRATEGIES.NETWORK_ONLY:
      return networkOnly(request);
    
    case CACHE_STRATEGIES.STALE_WHILE_REVALIDATE:
      return staleWhileRevalidate(request);
    
    default:
      return networkFirst(request);
  }
}

// Stratégie Cache First
async function cacheFirst(request) {
  try {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      console.log('[SW] Cache hit:', request.url);
      return cachedResponse;
    }
    
    console.log('[SW] Cache miss, fetch from network:', request.url);
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('[SW] Cache first error:', error);
    return getOfflineResponse(request);
  }
}

// Stratégie Network First
async function networkFirst(request) {
  try {
    console.log('[SW] Network first:', request.url);
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('[SW] Network failed, trying cache:', request.url);
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    return getOfflineResponse(request);
  }
}

// Stratégie Cache Only
async function cacheOnly(request) {
  const cache = await caches.open(CACHE_NAME);
  const cachedResponse = await cache.match(request);
  
  if (cachedResponse) {
    return cachedResponse;
  }
  
  return getOfflineResponse(request);
}

// Stratégie Network Only
async function networkOnly(request) {
  try {
    return await fetch(request);
  } catch (error) {
    return getOfflineResponse(request);
  }
}

// Stratégie Stale While Revalidate
async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_NAME);
  const cachedResponse = await cache.match(request);
  
  // Mise à jour en arrière-plan
  const fetchPromise = fetch(request).then(response => {
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  }).catch(() => {
    // Ignore network errors for background updates
  });
  
  // Retourner la version cache immédiatement si disponible
  if (cachedResponse) {
    return cachedResponse;
  }
  
  // Sinon attendre la réponse réseau
  try {
    return await fetchPromise;
  } catch (error) {
    return getOfflineResponse(request);
  }
}

// Réponse hors ligne
function getOfflineResponse(request) {
  const url = new URL(request.url);
  
  // Pages HTML - rediriger vers page offline
  if (request.headers.get('accept').includes('text/html')) {
    return caches.match(OFFLINE_URL);
  }
  
  // Images - retourner placeholder
  if (request.headers.get('accept').includes('image/')) {
    return new Response(
      '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">' +
      '<rect width="200" height="200" fill="#f3f4f6"/>' +
      '<text x="100" y="100" font-family="Arial" font-size="14" fill="#6b7280" text-anchor="middle" dominant-baseline="middle">' +
      'Image non disponible' +
      '</text></svg>',
      {
        headers: {
          'Content-Type': 'image/svg+xml',
          'Cache-Control': 'no-cache'
        }
      }
    );
  }
  
  // API - retourner erreur JSON
  if (url.pathname.startsWith('/api/')) {
    return new Response(
      JSON.stringify({
        error: 'Pas de connexion internet',
        offline: true
      }),
      {
        headers: {
          'Content-Type': 'application/json'
        },
        status: 503
      }
    );
  }
  
  // Autres ressources
  return new Response('Service non disponible hors ligne', {
    status: 503,
    statusText: 'Service Unavailable'
  });
}

// Gestion des notifications push
self.addEventListener('push', event => {
  console.log('[SW] Push reçu:', event);
  
  const options = {
    body: 'Vous avez des nouvelles sur VGK !',
    icon: '/static/images/icons/icon-192x192.png',
    badge: '/static/images/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Voir',
        icon: '/static/images/icons/action-explore.png'
      },
      {
        action: 'close',
        title: 'Fermer',
        icon: '/static/images/icons/action-close.png'
      }
    ],
    requireInteraction: true,
    silent: false
  };
  
  if (event.data) {
    try {
      const payload = event.data.json();
      options.body = payload.body || options.body;
      options.title = payload.title || 'Vidé-Grenier Kamer';
      options.data = { ...options.data, ...payload.data };
    } catch (error) {
      console.error('[SW] Erreur parsing push data:', error);
    }
  }
  
  event.waitUntil(
    self.registration.showNotification('Vidé-Grenier Kamer', options)
  );
});

// Gestion des clics sur notifications
self.addEventListener('notificationclick', event => {
  console.log('[SW] Notification click:', event);
  
  event.notification.close();
  
  if (event.action === 'close') {
    return;
  }
  
  // Déterminer l'URL à ouvrir
  let urlToOpen = '/';
  
  if (event.action === 'explore') {
    urlToOpen = '/products/';
  } else if (event.notification.data && event.notification.data.url) {
    urlToOpen = event.notification.data.url;
  }
  
  event.waitUntil(
    clients.matchAll({
      type: 'window'
    }).then(windowClients => {
      // Chercher une fenêtre existante
      for (let client of windowClients) {
        if (client.url.includes(self.location.origin)) {
          return client.focus().then(() => {
            return client.navigate(urlToOpen);
          });
        }
      }
      
      // Ouvrir nouvelle fenêtre
      return clients.openWindow(urlToOpen);
    })
  );
});

// Synchronisation en arrière-plan
self.addEventListener('sync', event => {
  console.log('[SW] Background sync:', event.tag);
  
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

// Fonction de synchronisation
async function doBackgroundSync() {
  try {
    // Synchroniser les données critiques
    await syncPendingMessages();
    await syncFavorites();
    await syncAnalytics();
    
    console.log('[SW] Background sync completed');
  } catch (error) {
    console.error('[SW] Background sync error:', error);
  }
}

// Synchroniser les messages en attente
async function syncPendingMessages() {
  // Implémentation de la synchronisation des messages
  console.log('[SW] Syncing pending messages...');
}

// Synchroniser les favoris
async function syncFavorites() {
  // Implémentation de la synchronisation des favoris
  console.log('[SW] Syncing favorites...');
}

// Synchroniser les analytics
async function syncAnalytics() {
  // Implémentation de la synchronisation des analytics
  console.log('[SW] Syncing analytics...');
}

// Nettoyage périodique du cache
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'CLEAN_CACHE') {
    event.waitUntil(cleanCache());
  }
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Fonction de nettoyage du cache
async function cleanCache() {
  try {
    const cache = await caches.open(CACHE_NAME);
    const requests = await cache.keys();
    
    const now = Date.now();
    const maxAge = 7 * 24 * 60 * 60 * 1000; // 7 jours
    
    for (const request of requests) {
      const response = await cache.match(request);
      const dateHeader = response.headers.get('date');
      
      if (dateHeader) {
        const responseDate = new Date(dateHeader).getTime();
        if (now - responseDate > maxAge) {
          await cache.delete(request);
          console.log('[SW] Cached resource cleaned:', request.url);
        }
      }
    }
    
    console.log('[SW] Cache cleaning completed');
  } catch (error) {
    console.error('[SW] Cache cleaning error:', error);
  }
}

// Mise à jour du Service Worker
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'CHECK_UPDATE') {
    event.waitUntil(
      self.registration.update().then(() => {
        console.log('[SW] Update check completed');
      })
    );
  }
});

// Partage de contenu
self.addEventListener('share', event => {
  console.log('[SW] Share event:', event);
  
  event.waitUntil(
    (async () => {
      const formData = await event.request.formData();
      const title = formData.get('title');
      const text = formData.get('text');
      const url = formData.get('url');
      
      // Traiter le contenu partagé
      // Rediriger vers la page de création de produit avec données pré-remplies
      const shareUrl = `/products/create/?shared=true&title=${encodeURIComponent(title)}&text=${encodeURIComponent(text)}`;
      
      return Response.redirect(shareUrl, 303);
    })()
  );
});

console.log('[SW] Service Worker VGK initialisé');