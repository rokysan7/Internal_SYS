# CheckList.md

CS Case 관리 시스템 개발 체크리스트. 위에서부터 순서대로 진행한다.

---

## Phase 0: 프로젝트 초기화

- [ ] Backend 디렉토리 생성 및 Python 가상환경 세팅
- [ ] `requirements.txt` 작성 (fastapi, uvicorn, sqlalchemy, psycopg2-binary, alembic, celery, redis)
- [ ] Frontend 디렉토리 생성 (`npx create-react-app frontend` 또는 Vite)
- [ ] Frontend 의존성 설치 (axios, react-router-dom)
- [ ] PostgreSQL 데이터베이스 생성
- [ ] `.gitignore` 작성 (venv, node_modules, __pycache__, .env)
- [ ] `.env` 파일 생성 (DB URL, Redis URL, Secret Key)

---

## Phase 1: Backend 코어 - DB 모델 및 기본 API

### 1-1. 데이터베이스 설정
- [ ] `database.py` 작성 (SessionLocal, engine, get_db)
- [ ] `models.py` 작성 - SQLAlchemy ORM 모델 전체
  - [ ] Enum 정의: UserRole(CS/ENGINEER/ADMIN), CaseStatus, Priority, NotificationType
  - [ ] User 모델
  - [ ] Product 모델
  - [ ] License 모델 (FK → Product)
  - [ ] ProductMemo 모델 (FK → Product, User)
  - [ ] LicenseMemo 모델 (FK → License, User)
  - [ ] CSCase 모델 (FK → Product, License, User)
  - [ ] Comment 모델 (FK → CSCase, User)
  - [ ] Checklist 모델 (FK → CSCase)
  - [ ] Notification 모델 (FK → User, CSCase nullable)
- [ ] Alembic 초기화 및 첫 마이그레이션 실행
- [ ] 테스트 데이터 시드 스크립트 작성

### 1-2. Pydantic 스키마
- [ ] `schemas.py` 작성 - 요청/응답 스키마 정의
  - [ ] User, Product, License 스키마
  - [ ] ProductMemo, LicenseMemo 스키마
  - [ ] CSCase 생성/수정/목록 스키마
  - [ ] Comment, Checklist 스키마
  - [ ] Notification 스키마

### 1-3. CRUD API 라우터
- [ ] `main.py` - FastAPI 앱 엔트리포인트 + CORS 설정
- [ ] `routers/products.py` - Product CRUD
  - [ ] `GET /products` (검색 가능)
  - [ ] `POST /products`
  - [ ] `GET /products/{id}`
  - [ ] `GET /products/{id}/licenses`
- [ ] `routers/licenses.py` - License CRUD
  - [ ] `POST /licenses`
  - [ ] `GET /licenses/{id}`
- [ ] `routers/memos.py` - Memo CRUD
  - [ ] `GET /products/{id}/memos`
  - [ ] `POST /products/{id}/memos`
  - [ ] `GET /licenses/{id}/memos`
  - [ ] `POST /licenses/{id}/memos`
- [ ] `routers/cases.py` - CS Case CRUD
  - [ ] `GET /cases`
  - [ ] `POST /cases`
  - [ ] `GET /cases/{id}`
  - [ ] `PUT /cases/{id}`
  - [ ] `PATCH /cases/{id}/status`
- [ ] `routers/comments.py` - Comment CRUD
  - [ ] `GET /cases/{id}/comments`
  - [ ] `POST /cases/{id}/comments`
- [ ] `routers/checklists.py` - Checklist CRUD
  - [ ] `GET /cases/{id}/checklists`
  - [ ] `POST /cases/{id}/checklists`
  - [ ] `PATCH /checklists/{id}`
- [ ] Swagger UI (`/docs`)에서 전체 CRUD 동작 확인

---

## Phase 2: Backend 확장 - 인증, 알림, 통계

### 2-1. 인증
- [ ] `routers/auth.py` 작성
  - [ ] `POST /auth/login`
  - [ ] `GET /auth/me`
- [ ] JWT 또는 세션 기반 인증 구현
- [ ] User.role 기반 접근 제어 미들웨어

### 2-2. Notification API
- [ ] `routers/notifications.py` 작성
  - [ ] `GET /notifications` (미읽음 필터링 지원)
  - [ ] `PATCH /notifications/{id}/read`
- [ ] CS Case 담당자 지정 시 알림 자동 생성
- [ ] 댓글 작성 시 담당자 알림 자동 생성

### 2-3. 통계 API
- [ ] `routers/statistics.py` 작성
  - [ ] `GET /cases/statistics?by=assignee` - 담당자별 미처리/완료 건수
  - [ ] `GET /cases/statistics?by=status` - 상태별 건수
  - [ ] `GET /cases/statistics?by=time` - 평균 처리 시간

### 2-4. 유사 문의 추천
- [ ] `GET /cases/similar?query=xxx` 구현
  - [ ] 제목/내용 기반 과거 CS 케이스 검색
  - [ ] 반환값: `[{id, title, status, assignee_id}]`

---

## Phase 3: Backend 비동기 - Celery + Redis

- [ ] Redis 설치 및 실행 확인
- [ ] `celery_app.py` 작성 (브로커: Redis)
- [ ] `tasks.py` 작성
  - [ ] `check_pending_cases` - 24시간 미처리 CS 리마인드 알림
  - [ ] `notify_comment` - 댓글 등록 시 담당자 알림
- [ ] Celery beat 주기 태스크 설정 (1시간마다 미처리 체크)
- [ ] Comment 라우터에서 `notify_comment.delay()` 호출 연동
- [ ] Celery worker + beat 정상 동작 확인

---

## Phase 4: Frontend 코어 - 기본 페이지 구현

### 4-1. 프로젝트 구조 세팅
- [ ] `src/api/` 디렉토리 - Axios API 모듈
  - [ ] `cases.js` (getCases, getCase, createCase, updateCaseStatus, getSimilarCases)
  - [ ] `products.js` (getProducts, getProduct, getProductLicenses, createProduct)
  - [ ] `licenses.js` (getLicense, createLicense, getLicenseMemos)
  - [ ] `memos.js` (getProductMemos, createProductMemo, getLicenseMemos, createLicenseMemo)
  - [ ] `notifications.js` (getNotifications, markAsRead)
- [ ] `API_BASE` 환경변수 설정

### 4-2. 라우팅 및 레이아웃
- [ ] `App.jsx` - React Router 설정
- [ ] 공통 레이아웃 (네비게이션, 사이드바)

### 4-3. 기본 페이지 구현
- [ ] `pages/Dashboard.jsx` - CS 현황 요약 + 내 담당 CS 목록
- [ ] `pages/CasePage.jsx` - CS Case 목록/상세/생성
- [ ] `pages/ProductPage.jsx` - Product 검색 + License 통합 뷰
- [ ] `pages/LicensePage.jsx` - License 상세 + 메모

### 4-4. 컴포넌트 구현
- [ ] `components/CaseList.jsx` - CS Case 목록 표시
- [ ] `components/CaseDetail.jsx` - CS Case 상세 (댓글, 체크리스트 포함)
- [ ] `components/CaseForm.jsx` - CS Case 생성 폼
- [ ] `components/ProductSearch.jsx` - Product 검색
- [ ] `components/LicenseDetail.jsx` - License 상세 + 메모 표시
- [ ] `components/MemoList.jsx` - 메모 목록/작성

---

## Phase 5: Frontend 확장 - 알림, AI 추천, 통계

- [ ] Notification Badge - 미읽음 알림 수 표시 (주기적 fetch)
- [ ] 알림 목록 UI (읽음/미읽음 구분, 클릭 시 읽음 처리)
- [ ] CaseForm AI 추천 연결 - 제목 입력 시 `/cases/similar` 호출
- [ ] 업무 통계 카드 (담당자별 미처리/완료 건수, 평균 처리 시간)
- [ ] Dashboard 상단에 통계 카드 배치

---

## Phase 6: 통합 테스트

- [ ] API ↔ React UI 통합 동작 확인
  - [ ] CRUD 전체 흐름 (생성 → 조회 → 수정 → 삭제)
  - [ ] 댓글 등록 → 알림 생성 → Badge 갱신
  - [ ] 메모 작성 → 조회
- [ ] 알림 시나리오 테스트
  - [ ] 댓글 등록 → 담당자 알림 생성 → Badge 반영
  - [ ] 미처리 CS 리마인드 → Notification 생성 → Badge 반영
- [ ] Celery Task 정상 동작 확인 (Redis 브로커, 태스크 상태)
- [ ] 페이지 간 네비게이션 및 데이터 흐름 확인

---

## Phase 7: Telegram 알림 연동

- [ ] Telegram Bot 생성 및 토큰 발급
- [ ] 사용자 ID ↔ Telegram chat_id 매핑
- [ ] Celery Task에서 Telegram 메시지 발송 구현
  - [ ] 담당자 지정 알림
  - [ ] 미처리 CS 리마인드
  - [ ] 댓글 알림
- [ ] 사용자별 알림 ON/OFF 설정
- [ ] 실제 Telegram 메시지 수신 확인

---

## Phase 8: 선택 확장

- [ ] FAQ 후보 자동 추천 (완료된 CS Case 태그 기반)
- [ ] 관리자 통계 페이지 (월별 처리량, 담당자별 처리 속도)
- [ ] Excel/CSV Export 기능
- [ ] Slack / Email 알림 연동
- [ ] AI 자동 분류/태그 추천 (NLP 기반)
