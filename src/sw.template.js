/* 오프라인 동작.
   버전 문자열은 빌드할 때 파일 내용 해시로 채워진다.
   버전이 바뀌면 예전 캐시를 지우므로, 새로 배포한 것이 확실히 반영된다. */
const V = '__VERSION__';
const CORE = __CORE__;

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(V)
      .then(c => c.addAll(CORE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== V).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;

  let url;
  try { url = new URL(req.url); } catch (_) { return; }
  if (url.origin !== location.origin) return;   // 남의 주소는 건드리지 않는다

  // 화면 자체는 새 것을 먼저 받아본다. 안 되면 저장해 둔 것을 쓴다.
  if (req.mode === 'navigate' || req.destination === 'document') {
    e.respondWith(
      fetch(req)
        .then(res => {
          const copy = res.clone();
          caches.open(V).then(c => c.put('./', copy));
          return res;
        })
        .catch(() => caches.match('./').then(r => r || caches.match('./index.html')))
    );
    return;
  }

  // 글꼴·아이콘은 바뀌지 않으므로 저장해 둔 것을 먼저 쓴다.
  e.respondWith(
    caches.match(req).then(hit => hit || fetch(req).then(res => {
      if (res && res.ok) {
        const copy = res.clone();
        caches.open(V).then(c => c.put(req, copy));
      }
      return res;
    }))
  );
});
