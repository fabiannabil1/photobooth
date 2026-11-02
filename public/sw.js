// Promaha Booth Progressive Web App Service Worker
const CACHE_NAME = 'promaha-booth-v1';

const STATIC_PRECACHE = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png',
  './icons/favicon.svg',
  './backgrounds/studio.jpg',
  './backgrounds/cyberpunk.jpg',
  './backgrounds/cafe.jpg',
  './backgrounds/sunset.jpg',
  './backgrounds/penthouse.jpg',
  './backgrounds/y2k.jpg',
  './frames/pantau-4-cut.webp',
  './frames/pantau-grid-2x2.webp',
  './frames/pantau-single.webp',
  './frames/film-4-cut.webp',
  './frames/film-grid-2x2.webp',
  './frames/film-single.webp',
  './frames/desa-4-cut.webp',
  './frames/desa-grid-2x2.webp',
  './frames/desa-single.webp',
  './frames/toga-4-cut.webp',
  './frames/toga-grid-2x2.webp',
  './frames/toga-single.webp',
  './frames/bloom-4-cut.webp',
  './frames/bloom-grid-2x2.webp',
  './frames/bloom-single.webp',
  './frames/expo-4-cut.webp',
  './frames/expo-grid-2x2.webp',
  './frames/expo-single.webp',
  './stickers/maskot.webp',
  './stickers/maskot-kamera.webp',
  './stickers/maskot-kepala.webp',
  './stickers/maskot-sepeda.webp',
  './stickers/logo.webp',
  './stickers/halo.webp',
  './stickers/sehat.webp',
  './stickers/pantau.webp',
  './stickers/aplikasi.webp',
  './stickers/kaki.webp',
  './stickers/aloebite.webp',
  './stickers/blue-bloom.webp',
  './stickers/kader.webp',
  './stickers/toga.webp',
  './stickers/telang.webp',
  './stickers/lidah-buaya.webp',
  './brand/logo.webp',
  './brand/maskot.webp',
  './brand/maskot-flip.webp',
  './backgrounds/promaha-backdrop.jpg',
  './backgrounds/promaha-desa.jpg',
  './backgrounds/promaha-dinding.jpg'
];

// Install: Cache core app shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async (cache) => {
      // Add assets with individual error resilience
      await Promise.allSettled(
        STATIC_PRECACHE.map((url) =>
          cache.add(url).catch((err) => {
            console.warn(`[SW] Precache failed for ${url}:`, err);
          })
        )
      );
    })
  );
  self.skipWaiting();
});

// Activate: Clean up outdated caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((name) => {
          if (name !== CACHE_NAME) {
            console.log(`[SW] Removing legacy cache: ${name}`);
            return caches.delete(name);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch: Smart caching strategy
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Only handle GET requests
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // Ignore browser extensions or non-HTTP protocols
  if (!url.protocol.startsWith('http')) return;

  // 1. External MediaPipe & Google Fonts CDN assets: Cache-First
  const isCdn = url.hostname.includes('jsdelivr.net') || 
                url.hostname.includes('fonts.googleapis.com') || 
                url.hostname.includes('fonts.gstatic.com');

  if (isCdn) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) return cachedResponse;

        return fetch(request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseToCache);
            });
          }
          return networkResponse;
        }).catch(() => cachedResponse);
      })
    );
    return;
  }

  // 2. Navigation / HTML Document: Network-First with Cache Fallback
  if (request.mode === 'navigate' || request.destination === 'document') {
    event.respondWith(
      fetch(request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseToCache);
            });
          }
          return networkResponse;
        })
        .catch(async () => {
          const cached = await caches.match(request);
          if (cached) return cached;
          return caches.match('./index.html') || caches.match('./');
        })
    );
    return;
  }

  // 3. Static hashed Vite assets & local images: Stale-While-Revalidate
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      const fetchPromise = fetch(request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseToCache);
          });
        }
        return networkResponse;
      }).catch(() => null);

      return cachedResponse || fetchPromise;
    })
  );
});
