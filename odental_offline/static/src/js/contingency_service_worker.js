"use strict";

const CACHE_NAME = "odental-contingency-shell-v1";
const SHELL_URLS = ["/odental/contingency", "/odental/contingency/app.js"];

async function cacheShell() {
    const cache = await caches.open(CACHE_NAME);
    await Promise.all(SHELL_URLS.map(async (url) => {
        try {
            const response = await fetch(url, {credentials: "include", cache: "no-cache"});
            if (response.ok && !response.redirected) await cache.put(url, response.clone());
        } catch (error) {
            // An older valid shell remains available when the network is down.
        }
    }));
}

self.addEventListener("install", (event) => {
    event.waitUntil(cacheShell().then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) => Promise.all(
            keys.filter((key) => key.startsWith("odental-contingency-shell-") && key !== CACHE_NAME)
                .map((key) => caches.delete(key))
        )).then(() => self.clients.claim())
    );
});

self.addEventListener("message", (event) => {
    if (event.data && event.data.type === "CACHE_SHELL") event.waitUntil(cacheShell());
});

self.addEventListener("fetch", (event) => {
    if (event.request.method !== "GET") return;
    const url = new URL(event.request.url);
    if (url.origin !== self.location.origin || !SHELL_URLS.includes(url.pathname)) return;
    event.respondWith((async () => {
        try {
            const response = await fetch(event.request);
            if (response.ok && !response.redirected) {
                const cache = await caches.open(CACHE_NAME);
                await cache.put(url.pathname, response.clone());
            }
            return response;
        } catch (error) {
            const cached = await caches.match(url.pathname);
            if (cached) return cached;
            return new Response("Modo de contingencia no preparado en este dispositivo.", {
                status: 503,
                headers: {"Content-Type": "text/plain; charset=utf-8"},
            });
        }
    })());
});

