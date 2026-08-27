self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open('egocrypto-v1').then((cache) => {
            return cache.addAll([
                '/',
                '/static/manifest.json',
                '/static/ai_robot.png'
            ]);
        })
    );
});

self.addEventListener('fetch', (e) => {
    e.respondWith(
        caches.match(e.request).then((response) => {
            return response || fetch(e.request);
        })
    );
});
