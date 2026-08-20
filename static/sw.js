/* Keeps a copy of the arcade on the phone so it opens instantly and survives
   a bad signal. Only the pages and artwork are stored - never the game itself,
   which always has to come fresh from the server. */

// Bump this whenever the pages change and you want phones to pick it up on the
// very next launch. Forgetting is not fatal - the copy below is refreshed in
// the background either way, so it would just arrive one launch later.
const CACHE = 'duo-arcade-shell-v2';

const SHELL = [
  '/',
  '/static/style.css',
  '/static/util.js',
  '/static/app.js',
  '/static/games/tictactoe.js',
  '/static/games/connect4.js',
  '/static/games/rps.js',
  '/static/games/memory.js',
  '/static/games/wordladder.js',
  '/static/games/dots.js',
  '/static/games/crosswires.js',
  '/static/games/bridges.js',
  '/static/games/gomoku.js',
  '/static/games/reversi.js',
  '/static/games/poker.js',
  '/static/games/xiangqi.js',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/apple-touch-icon.png',
  '/manifest.webmanifest',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      // one bad file shouldn't stop the rest being stored
      .then((cache) => Promise.allSettled(SHELL.map((url) => cache.add(url))))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((names) => Promise.all(
        names.filter((n) => n !== CACHE).map((n) => caches.delete(n))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // Anything to do with an actual game goes straight to the server, always.
  // Serving a stale board from a cache would be worse than showing nothing.
  if (url.pathname.startsWith('/api/')) return;
  if (url.origin !== self.location.origin) return;

  // Serve what we have immediately, then quietly refresh it for next time.
  // Waiting for the network here would mean staring at a blank screen whenever
  // the free server is waking up.
  event.respondWith(
    caches.match(request).then((hit) => {
      const fresh = fetch(request)
        .then((response) => {
          if (response && response.status === 200 && response.type === 'basic') {
            const copy = response.clone();
            caches.open(CACHE).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(() => hit);
      return hit || fresh;
    }),
  );
});
