# Web Push Notification 구현 체크리스트

> 기존 Notification 시스템(DB 저장 + 30초 폴링)은 유지하면서, OS 레벨 푸시 알림을 추가합니다.
> 각 항목에 [검증 결과]를 표기합니다: CONFIRMED, UPDATED, REMOVED

---

## Phase 1: Backend Infrastructure

- [x] **B1-1** VAPID 키 생성 및 환경 설정
  - `pywebpush` 패키지 설치 (`uv add pywebpush`)
  - VAPID 키 쌍 생성 (public/private)
  - `.env`에 `VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY`, `VAPID_CLAIMS_EMAIL` 추가
  - `services/push.py`에서 환경변수 직접 로드 또는 별도 `config.py` 생성 (DB 설정과 분리)

- [x] **B1-2** PushSubscription 모델 생성
  - `models.py`에 `PushSubscription` 테이블 추가
  - 필드: `id`, `user_id` (FK → users.id), `endpoint` (String, unique), `p256dh` (String), `auth` (String), `created_at`
  - User 모델에 `push_subscriptions` relationship 추가

- [x] **B1-3** DB 마이그레이션
  - `alembic revision --autogenerate -m "add push_subscriptions table"`
  - `alembic upgrade head`

- [x] **B1-4** Push 구독 API 엔드포인트 생성
  - `routers/push.py` 신규 생성
  - `schemas.py`에 `PushSubscriptionCreate(endpoint, p256dh, auth)`, VAPID 공개키 응답 스키마 추가
  - `POST /push/subscribe` — 구독 등록 (endpoint + keys 저장), `Depends(get_current_user)` 필수
  - `DELETE /push/unsubscribe` — 구독 해제 (endpoint 기준 삭제)
  - `GET /push/vapid-public-key` — 프론트에서 구독 시 사용할 VAPID 공개키 반환
  - `main.py`에 라우터 등록

---

## Phase 2: Frontend Infrastructure

- [x] **F2-1** Service Worker 생성
  - `frontend/public/sw.js` 파일 생성
  - `push` 이벤트 핸들러: payload에서 title/body/case_id 추출 → `self.registration.showNotification()` 호출
  - `notificationclick` 이벤트 핸들러: 알림 클릭 시 해당 케이스 페이지(`/cases/{case_id}`)로 이동, 이미 열린 탭이 있으면 해당 탭으로 포커스

- [x] **F2-2** Service Worker 등록
  - `main.jsx`에서 `navigator.serviceWorker.register('/sw.js')` 호출
  - HTTPS 또는 localhost 환경 체크

- [x] **F2-3** Push 구독 유틸리티 생성
  - `src/api/push.js` 신규 생성
  - `subscribePush()`: 알림 권한 요청 → SW 등록 → `pushManager.subscribe()` → 백엔드 POST `/push/subscribe`
  - `unsubscribePush()`: 구독 해제 → 백엔드 DELETE `/push/unsubscribe`
  - VAPID 공개키는 `GET /push/vapid-public-key`에서 가져오기
  - `urlBase64ToUint8Array()` 유틸 함수 생성 — VAPID 공개키 base64 → `Uint8Array` 변환 (`applicationServerKey`용)

- [x] **F2-4** 알림 권한 UI 추가
  - `Layout.jsx` topbar에 알림 활성화/비활성화 토글 버튼 추가
  - 상태: granted(활성) / denied(차단됨-설정 안내) / default(미설정-요청 가능)
  - `Notification.permission` 체크하여 UI 상태 반영

---

## Phase 3: Celery → Web Push 연동

- [x] **B3-1** Web Push 전송 유틸리티 함수 생성
  - `services/push.py` 신규 생성
  - `send_push_to_user(db, user_id, title, body, case_id)` 함수
  - 해당 user의 모든 PushSubscription 조회 → 각각 `webpush()` 호출
  - 만료/무효 구독(410 Gone, 404) 자동 삭제 (cleanup)
  - 전송 실패 시 에러 로그만 남기고 알림 생성은 영향 없도록 처리
  - B1-1에서 설정한 VAPID private key, claims email 환경변수 사용

- [x] **B3-2** Celery task에 Web Push 호출 추가
  - `notify_case_assigned`: DB 알림 생성 직후 `send_push_to_user()` 호출
  - `notify_comment`: 동일 패턴
  - `notify_reply`: 동일 패턴
  - `check_pending_cases`: 동일 패턴
  - payload 형식: `{ "title": "CS Dashboard", "body": message, "case_id": case.id }`

---

## Phase 4: Test & Documentation

- [x] **B4-1** 백엔드 테스트
  - 구독 등록/해제 API 테스트
  - `send_push_to_user()` 단위 테스트 (webpush mock)
  - 만료 구독 자동 삭제 테스트

- [ ] **B4-2** 브라우저 호환성 확인 *(수동 테스트 필요)*
  - Chrome (Mac/Windows) 동작 확인
  - Firefox (Mac/Windows) 동작 확인
  - Edge (Windows) 동작 확인
  - Safari (macOS 13+ / iOS 16.4+) 지원 여부 확인 및 제한사항 문서화

- [x] **F4-1** CLAUDE.md 업데이트
  - Reusable Modules에 `services/push.py`, `api/push.js`, `sw.js` 추가
  - Backend Utilities에 `send_push_to_user` 추가

---

## Summary

| Phase | Category | Backend | Frontend | Priority |
|-------|----------|---------|----------|----------|
| Phase 1 | Backend Infrastructure | 4 | 0 | Highest |
| Phase 2 | Frontend Infrastructure | 0 | 4 | High |
| Phase 3 | Celery 연동 | 2 | 0 | High |
| Phase 4 | Test & Docs | 2 | 1 | Medium |
| **Total** | | **8** | **5** | **13** |

### 기존 시스템 영향
| 항목 | 영향 |
|------|------|
| Notification 모델 | 변경 없음 |
| Celery tasks | `send_push_to_user()` 호출 1줄 추가 |
| 프론트 폴링 | 변경 없음 (Web Push와 병행) |
| DB | `push_subscriptions` 테이블 1개 추가 |

### 의존성 추가
| Layer | Package | Purpose |
|-------|---------|---------|
| Backend | `pywebpush` | Web Push 전송 |
| Frontend | 없음 | Push API는 브라우저 내장 |
