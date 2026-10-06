// Progressive Web App (PWA) Controller
// Handles Service Worker registration, install prompts, and online/offline status

export function initPWA() {
  // 1. Register Service Worker
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      // Use relative path for GitHub Pages and subpaths compatibility
      navigator.serviceWorker
        .register('./sw.js')
        .then((registration) => {
          console.log('[PWA] Service Worker active, scope:', registration.scope);

          // Check for worker updates
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            if (newWorker) {
              newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                  console.log('[PWA] Update ready. Restart/refresh to apply.');
                }
              });
            }
          });
        })
        .catch((error) => {
          console.warn('[PWA] Service Worker registration failed:', error);
        });
    });
  }

  // 2. Custom Install Button UI
  let deferredPrompt = null;
  const installBtn = document.getElementById('btnInstallApp');

  window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent default mini-infobar on mobile Chrome
    e.preventDefault();
    deferredPrompt = e;

    if (installBtn) {
      installBtn.style.display = 'inline-flex';
    }
  });

  if (installBtn) {
    installBtn.addEventListener('click', async () => {
      if (!deferredPrompt) return;

      installBtn.disabled = true;
      try {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        console.log(`[PWA] Install prompt outcome: ${outcome}`);
        if (outcome === 'accepted') {
          installBtn.style.display = 'none';
        }
      } catch (err) {
        console.error('[PWA] Install prompt error:', err);
      } finally {
        installBtn.disabled = false;
        deferredPrompt = null;
      }
    });
  }

  window.addEventListener('appinstalled', () => {
    console.log('[PWA] Lumi Booth installed successfully!');
    if (installBtn) {
      installBtn.style.display = 'none';
    }
  });

  // 3. Online / Offline Indicators
  window.addEventListener('offline', () => {
    console.warn('[PWA] Connection lost. Running in offline mode.');
  });

  window.addEventListener('online', () => {
    console.log('[PWA] Connection restored.');
  });
}
