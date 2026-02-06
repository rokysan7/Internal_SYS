# Web Push Notification 구현 노트

## 구현 개요

CS Dashboard에 OS 레벨 알림(데스크톱 푸시 알림)을 추가하여, 케이스 배정/댓글/리마인더 발생 시 사용자가 브라우저를 보고 있지 않아도 알림을 받을 수 있도록 구현.

---

## 아키텍처

```
[이벤트 발생] → [Celery Task] → [DB Notification 생성] + [Web Push 전송(FCM)]
                                         ↓
                              [Frontend 30초 폴링]
                                         ↓
                              [새 알림 감지 → OS Notification 표시]
```

### 구성 요소

| 계층 | 파일 | 역할 |
|------|------|------|
| Backend | `services/push.py` | pywebpush로 FCM에 Web Push 전송 |
| Backend | `routers/push.py` | 구독 CRUD API + VAPID 공개키 제공 |
| Backend | `tasks.py` | Celery 비동기 태스크에서 DB 알림 생성 후 push 호출 |
| Backend | `models.py` | `PushSubscription` 테이블 (endpoint, p256dh, auth) |
| Frontend | `public/sw.js` | Service Worker — push 이벤트 수신 시 showNotification |
| Frontend | `src/api/push.js` | subscribe/unsubscribe/status API 유틸 |
| Frontend | `src/components/Layout.jsx` | 푸시 토글 UI + 폴링 기반 OS 알림 fallback |
| Infra | `.env` | VAPID 키 쌍, claims email |
| Infra | `certs/` | mkcert로 생성한 HTTPS 인증서 |

---

## HTTPS 환경 구성

Web Push API는 HTTPS(또는 localhost)에서만 동작하므로 개발 환경에 HTTPS를 적용.

### mkcert 인증서 생성

```bash
mkcert -install
mkcert -key-file certs/key.pem -cert-file certs/cert.pem localhost 192.168.0.64
```

### Vite HTTPS + Proxy 설정 (`vite.config.js`)

```javascript
const httpsConfig =
  fs.existsSync(keyPath) && fs.existsSync(certPath)
    ? { key: fs.readFileSync(keyPath), cert: fs.readFileSync(certPath) }
    : undefined;

export default defineConfig({
  server: {
    https: httpsConfig,
    host: '0.0.0.0',
    proxy: httpsConfig ? buildProxy(apiPaths, 'http://localhost:8002') : undefined,
  },
});
```

HTTPS 모드일 때 Vite 프록시가 API 요청을 백엔드(HTTP)로 중계하여 Mixed Content를 방지.

---

## 발생한 문제와 해결

### 1. Mixed Content — VITE_API_BASE 하드코딩

**증상**: HTTPS 페이지에서 모든 API 호출이 차단됨 (ERR_BLOCKED_BY_CLIENT)

**원인**: `frontend/.env`에 `VITE_API_BASE=http://192.168.0.64:8002`가 설정되어 있어, `client.js`의 프로토콜 자동 감지 로직이 무시됨.

**해결**: `.env`에서 `VITE_API_BASE`를 주석 처리. HTTPS일 때 빈 baseURL → Vite 프록시 경유.

```javascript
// client.js의 자동 감지 로직
const API_BASE =
  import.meta.env.VITE_API_BASE ||
  (window.location.protocol === 'https:' ? '' : 'http://localhost:8002');
```

---

### 2. Mixed Content — FastAPI 307 Redirect

**증상**: `/notifications` 등 일부 API에서 Mixed Content 에러 지속

**원인**: FastAPI의 `redirect_slashes=True`(기본값)가 `/notifications` → `http://localhost:8002/notifications/`로 307 리다이렉트. Location 헤더가 절대 HTTP URL이라 브라우저가 차단.

**해결**: Vite 프록시에 `configure` 핸들러를 추가하여 Location 헤더를 상대 경로로 변환.

```javascript
configure(proxyServer) {
  proxyServer.on('proxyRes', (proxyRes) => {
    const location = proxyRes.headers['location'];
    if (location) {
      try {
        const url = new URL(location);
        proxyRes.headers['location'] = url.pathname + url.search;
      } catch { /* relative URL — keep as-is */ }
    }
  });
},
```

---

### 3. SPA 라우트와 API 경로 충돌

**증상**: 브라우저에서 `/cases`를 직접 접근하면 빈 페이지 (API 응답이 반환됨)

**원인**: `/cases`가 SPA 라우트이자 API 프록시 경로. 브라우저 네비게이션(HTML 요청)까지 프록시가 가로챔.

**해결**: `bypass` 함수에서 `Accept: text/html` 요청은 SPA로 전달.

```javascript
bypass(req) {
  if (req.headers.accept?.includes('text/html')) {
    return '/index.html';
  }
},
```

---

### 4. VAPID 키 형식 오류

**증상**: Celery 태스크는 성공하지만 push가 전송되지 않음 (에러가 조용히 무시됨)

**원인**: `.env`의 `VAPID_PRIVATE_KEY`가 PEM 형식(246자)으로 저장되어 있었음. `pywebpush`는 raw base64url 형식(43자)을 요구.

**해결**: 올바른 형식으로 키 쌍 재생성.

```python
# 키 생성 스크립트
from py_vapid import Vapid
v = Vapid()
v.generate_keys()
print("private:", v.private_pem())  # ← 이것이 아니라
print("private:", v.private_key)     # ← raw base64url (43자) 필요
```

```env
# .env — 올바른 형식
VAPID_PRIVATE_KEY=JaDKm3VNy2JJsf2P8c7qIgHPA3qleEgdVfAxqcpALmQ     # 43자
VAPID_PUBLIC_KEY=BBUVE9x35dHp7ZImHRqgPSxdUExb0-9aXAaVA85KER6k...   # 87자
VAPID_CLAIMS_EMAIL=mailto:admin@cs-dashboard.local
```

---

### 5. FCM이 201 반환하지만 실제 전달 안 됨

**증상**: `pywebpush` → FCM 201 성공, 하지만 Chrome에 push 이벤트 미도착

**진단**:
- `chrome://gcm-internals/` → GCM CONNECTED, READY 상태이나 **Receive Message Log 비어 있음**
- DevTools Application > Service Workers > Push 버튼으로 수동 테스트 시 알림 정상 표시
- `content_encoding` aes128gcm / aesgcm 모두 동일 증상
- VAPID JWT claims (aud, exp, sub) 정상 확인
- 구독 endpoint, applicationServerKey 모두 DB와 일치

**결론**: FCM 레거시 엔드포인트(`fcm.googleapis.com/fcm/send/...`)가 메시지를 수락(201)하지만 실제로 Chrome에 전달하지 않는 문제. FCM 서버 측 이슈로 클라이언트에서 해결 불가.

**우회 해결**: 폴링 기반 OS 알림 fallback 구현 (아래 참조).

---

## 최종 해결: 폴링 기반 OS 알림 Fallback

FCM 전달 불안정 문제를 우회하기 위해, 기존 30초 폴링에서 **새로 등장한 미읽은 알림을 감지하면 OS Notification을 직접 표시**하는 방식을 구현.

### 핵심 로직 (`Layout.jsx`)

```javascript
// 이미 본 알림 ID 추적
const seenIdsRef = useRef(new Set());

// 폴링 시 새 알림 감지
if (seenIdsRef.current.size === 0) {
  // 첫 로드: 기존 알림을 모두 seen 처리 (중복 알림 방지)
  data.forEach((n) => seenIdsRef.current.add(n.id));
} else {
  data.forEach((n) => {
    if (!n.is_read && !seenIdsRef.current.has(n.id)) {
      showOSNotification(n);  // OS 알림 표시
    }
    seenIdsRef.current.add(n.id);
  });
}
```

```javascript
// OS 알림 표시 (SW 우선, fallback으로 Notification API)
function showOSNotification(notification) {
  if (Notification.permission !== 'granted') return;

  const options = {
    body: notification.message,
    icon: '/favicon.ico',
    tag: `notif-${notification.id}`,  // 동일 알림 중복 방지
    data: { case_id: notification.case_id },
  };

  if (navigator.serviceWorker?.controller) {
    navigator.serviceWorker.ready.then((reg) =>
      reg.showNotification('CS Dashboard', options)
    );
  } else {
    new Notification('CS Dashboard', options);
  }
}
```

### 동작 특성

| 상황 | 알림 방식 | 지연 시간 |
|------|-----------|----------|
| 페이지 열려 있음 | 폴링 → OS Notification | 최대 30초 |
| 페이지 닫혀 있음 | FCM Web Push (best-effort) | 즉시 (전달 시) |
| 알림 권한 미허용 | 인앱 알림 패널만 | 최대 30초 |

---

## 디버깅 팁

### 브라우저 콘솔에서 확인

```javascript
// 알림 권한 상태
Notification.permission  // "granted" | "denied" | "default"

// Service Worker 상태
navigator.serviceWorker.controller  // active SW 객체 또는 null

// 현재 Push 구독 정보
const reg = await navigator.serviceWorker.ready;
const sub = await reg.pushManager.getSubscription();
console.log(sub?.endpoint);
console.log(btoa(String.fromCharCode(...new Uint8Array(sub?.getKey('p256dh')))));
```

### 백엔드 디버깅

```python
# services/push.py에 print 디버그 추가 후 Celery 로그 확인
print(f"[PUSH DEBUG] VAPID_PRIVATE_KEY length={len(VAPID_PRIVATE_KEY)}")
print(f"[PUSH DEBUG] Found {len(subscriptions)} subscriptions")
print(f"[PUSH DEBUG] FCM response: status={resp.status_code}")
```

### Chrome 내부 진단

- `chrome://gcm-internals/` — GCM 연결 상태, 수신 메시지 로그
- `chrome://serviceworker-internals/` — SW 등록/상태 확인
- DevTools > Application > Service Workers > Push 버튼 — SW push 핸들러 수동 테스트

---

## 파일 변경 요약

| 파일 | 변경 내용 |
|------|-----------|
| `frontend/.env` | VITE_API_BASE 주석 처리 |
| `frontend/vite.config.js` | HTTPS + proxy bypass + Location 헤더 rewrite |
| `frontend/src/components/Layout.jsx` | 폴링 기반 OS 알림 fallback, push 토글 UI |
| `frontend/public/sw.js` | push/notificationclick 이벤트 핸들러 |
| `frontend/src/api/push.js` | subscribe/unsubscribe/status API |
| `backend/.env` | VAPID 키 쌍 (base64url 형식) |
| `backend/services/push.py` | pywebpush 전송 + 만료 구독 정리 |
| `backend/routers/push.py` | 구독 CRUD + VAPID 공개키 API |
| `backend/models.py` | PushSubscription 모델 |
| `backend/schemas.py` | PushSubscription 스키마 |
| `backend/tasks.py` | 4개 Celery 태스크에 send_push_to_user 통합 |
| `backend/alembic/versions/37d794a...` | push_subscriptions 테이블 마이그레이션 |
