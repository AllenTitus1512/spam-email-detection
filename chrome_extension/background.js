// background service worker for MV3. Currently used for notification handling
// and any background tasks required by the extension.

self.addEventListener('install', (event) => {
  // Service worker installed
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  // Ready
  event.waitUntil(self.clients.claim());
});

// Optionally handle notification clicks
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  // Focus the extension popup or open the app
  event.waitUntil(clients.openWindow('/'));
});
