// Tunas Booth Progressive Web App Service Worker
const CACHE_NAME = 'tunas-booth-v3';

const STATIC_PRECACHE = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/apple-touch-icon.png',
  './icons/favicon.svg',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  './backgrounds/cafe.jpg',
  './backgrounds/cyberpunk.jpg',
  './backgrounds/filkom-dies62.jpg',
  './backgrounds/filkom-dinding.jpg',
  './backgrounds/filkom-kebun.jpg',
  './backgrounds/filkom-ladang.jpg',
  './backgrounds/penthouse.jpg',
  './backgrounds/studio.jpg',
  './backgrounds/sunset.jpg',
  './backgrounds/y2k.jpg',
  './frames/akar-4-cut.webp',
  './frames/akar-grid-2x2.webp',
  './frames/akar-single.webp',
  './frames/benih-4-cut.webp',
  './frames/benih-grid-2x2.webp',
  './frames/benih-single.webp',
  './frames/dies-4-cut.webp',
  './frames/dies-grid-2x2.webp',
  './frames/dies-single.webp',
  './frames/fasilkom-4-cut.webp',
  './frames/fasilkom-grid-2x2.webp',
  './frames/fasilkom-single.webp',
  './frames/film-4-cut.webp',
  './frames/film-grid-2x2.webp',
  './frames/film-single.webp',
  './frames/lab-4-cut.webp',
  './frames/lab-grid-2x2.webp',
  './frames/lab-single.webp',
  './frames/panen-data-4-cut.webp',
  './frames/panen-data-grid-2x2.webp',
  './frames/panen-data-single.webp',
  './stickers/chip.webp',
  './stickers/dies62.webp',
  './stickers/drone.webp',
  './stickers/gauge.webp',
  './stickers/halo.webp',
  './stickers/hidroponik.webp',
  './stickers/innovate.webp',
  './stickers/kilau.webp',
  './stickers/kode.webp',
  './stickers/laptop.webp',
  './stickers/logo-fasilkom.webp',
  './stickers/logo-lab.webp',
  './stickers/logo-unej.webp',
  './stickers/panen-data.webp',
  './stickers/sensor.webp',
  './stickers/tani-cerdas.webp',
  './stickers/terus-tumbuh.webp',
  './stickers/tunas-kecil.webp',
  './stickers/tunas-senang.webp',
  './stickers/tunas.webp',
  './stickers/ucapan-dies.webp',
  './stickers/wifi.webp',
  './brand/dies62.webp',
  './brand/fasilkom.webp',
  './brand/logo.webp',
  './brand/maskot-senang.webp',
  './brand/maskot.webp',
  './brand/unej.webp'
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
