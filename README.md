# CS Case Management Dashboard

> **Version**: v1.5.0

사내 고객지원(CS) 케이스를 관리하는 내부 운영 시스템. 제품/라이선스별 CS 케이스 추적, 댓글·체크리스트 협업, 알림, 업무 통계 기능을 제공한다.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy, Pydantic v2 |
| **Database** | PostgreSQL |
| **Async Tasks** | Celery + Redis |
| **Auth** | JWT (python-jose + passlib/bcrypt), Role-based access control |
| **Frontend** | React 19, Vite, Axios, React Router v7 |
| **Testing** | pytest, httpx, pytest-cov |

## Architecture

```
┌─────────────┐     HTTP/JSON     ┌──────────────┐     SQL      ┌────────────┐
│  React SPA  │ ←───────────────→ │  FastAPI API  │ ←──────────→ │ PostgreSQL │
│  (Vite)     │   Bearer JWT      │  12 Routers   │              │  12 Tables │
└─────────────┘                   └──────┬───────┘              └────────────┘
                                         │ .delay()
                                         ▼
                                  ┌──────────────┐
                                  │ Celery Worker │ ←── Redis Broker
                                  │ + Beat        │
                                  └──────────────┘
```

### Database Schema (12 Tables)

- **User** — 역할: CS / ENGINEER / ADMIN
- **Product** → has many **License**
- **ProductMemo** / **LicenseMemo** — 제품·라이선스별 지식 축적 (작성자 이름 표시)
- **CSCase** → belongs to Product, License; many-to-many **User**(assignees) via **case_assignees**; 조직 정보 (organization, org_phone, org_contact)
- **case_assignees** — 케이스-담당자 다대다 관계 테이블
- **Comment** — 내부/외부 구분 (`is_internal`), 중첩 답글 지원 (`parent_id`)
- **Checklist** — 케이스별 체크리스트 (작성자 추적: `author_id`)
- **Notification** — ASSIGNEE / REMINDER / COMMENT 타입
- **PushSubscription** — Web Push 구독 정보 (endpoint, p256dh, auth)
- **TagMaster** — 태그 자동 학습 및 추천 (keyword_weights)

## Authentication & Authorization

### Features
- **JWT Authentication**: Secure token-based login with Bearer token
- **Auto Logout**: 60-minute idle timeout (detects mouse, keyboard, scroll, touch)
- **Role-based Access Control**: CS, ENGINEER, ADMIN roles
- **Route Protection**: PrivateRoute (login required), AdminRoute (ADMIN only)
- **401 Interceptor**: Automatic redirect to login on token expiration

### Default Admin Account
| Email | Password |
|-------|----------|
| admin@monoflow.kr | 0000 |

### User Management (ADMIN only)
- User list with search, role filter, pagination
- Create/Edit/Deactivate users
- Password reset
- Self password change (all authenticated users)

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL
- Redis
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (Python 패키지 관리)

### Backend

```bash
cd backend

# 가상환경 생성 & 활성화
uv venv
source .venv/bin/activate

# 의존성 설치
uv pip install -r requirements.txt

# 환경변수 (.env 파일을 프로젝트 루트에 생성)
# DATABASE_URL=postgresql://<user>@localhost:5432/cs_dashboard
# REDIS_URL=redis://localhost:6379/0
# SECRET_KEY=<your-secret-key>

# DB 생성 & 마이그레이션
createdb cs_dashboard
alembic upgrade head

# (선택) 시드 데이터
python seed.py

# 서버 실행
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

### Celery Worker (비동기 알림)

```bash
cd backend
celery -A celery_app worker --loglevel=info    # Worker
celery -A celery_app beat --loglevel=info       # Beat (주기 태스크)
```

## API Endpoints

| Domain | Method | Path | Description |
|--------|--------|------|-------------|
| **Auth** | POST | `/auth/login` | JWT 로그인 |
| | GET | `/auth/me` | 현재 사용자 조회 |
| | POST | `/auth/change-password` | 비밀번호 변경 (본인) |
| **Admin** | GET | `/admin/users` | 회원 목록 (검색, 역할 필터, 페이지네이션) |
| | POST | `/admin/users` | 회원 생성 |
| | GET | `/admin/users/{id}` | 회원 상세 |
| | PUT | `/admin/users/{id}` | 회원 수정 |
| | DELETE | `/admin/users/{id}` | 회원 비활성화 (soft delete) |
| | POST | `/admin/users/{id}/reset-password` | 비밀번호 재설정 |
| **Products** | GET | `/products/` | 제품 목록 (검색, 페이지네이션, 정렬) |
| | POST | `/products/` | 제품 생성 |
| | POST | `/products/bulk` | CSV 일괄 업로드 (Product + License) |
| | GET | `/products/{id}` | 제품 상세 |
| | GET | `/products/{id}/licenses` | 제품별 라이선스 목록 |
| **Products** | PUT | `/products/{id}` | 제품 수정 (ADMIN) |
| | DELETE | `/products/{id}` | 제품 삭제 (ADMIN) |
| **Licenses** | POST | `/licenses/` | 라이선스 생성 |
| | GET | `/licenses/{id}` | 라이선스 상세 |
| | PUT | `/licenses/{id}` | 라이선스 수정 (ADMIN) |
| | DELETE | `/licenses/{id}` | 라이선스 삭제 (ADMIN) |
| **Memos** | GET/POST | `/products/{id}/memos` | 제품 메모 (JWT 인증) |
| | GET/POST | `/licenses/{id}/memos` | 라이선스 메모 (JWT 인증) |
| | DELETE | `/product-memos/{id}` | 제품 메모 삭제 (작성자/ADMIN) |
| | DELETE | `/license-memos/{id}` | 라이선스 메모 삭제 (작성자/ADMIN) |
| **Cases** | GET | `/cases/` | 케이스 목록 (status, assignee, product, requester 필터) |
| | POST | `/cases/` | 케이스 생성 (복수 담당자, 조직 정보 지원) |
| | GET | `/cases/{id}` | 케이스 상세 (복수 담당자 정보 포함) |
| | PUT | `/cases/{id}` | 케이스 수정 |
| | PATCH | `/cases/{id}/status` | 상태 변경 (DONE 완료시간, CANCEL 취소시간 자동 기록) |
| | DELETE | `/cases/{id}` | 케이스 삭제 (담당자/ADMIN, cascade) |
| | GET | `/cases/similar` | 유사 케이스 검색 (TF-IDF + 태그 유사도) |
| | GET | `/cases/{id}/similar` | 특정 케이스 유사 케이스 조회 (캐시 지원) |
| | GET | `/cases/my-progress` | 내 진행 현황 (상태별 건수, 기간 필터) |
| **Comments** | GET/POST | `/cases/{id}/comments` | 댓글 CRUD (N+1 최적화) |
| | DELETE | `/cases/{id}/comments/{cid}` | 댓글 삭제 (작성자/ADMIN) |
| **Checklists** | GET/POST | `/cases/{id}/checklists` | 체크리스트 CRUD (작성자 추적) |
| | PATCH | `/checklists/{id}` | 체크리스트 토글 |
| **Tags** | GET | `/tags/search` | 태그 검색 |
| | GET | `/tags/suggest` | 태그 추천 (키워드 기반) |
| **Notifications** | GET | `/notifications/` | 알림 목록 (user_id, unread 필터) |
| | PATCH | `/notifications/{id}/read` | 읽음 처리 |
| **Push** | POST | `/push/subscribe` | Web Push 구독 |
| | POST | `/push/unsubscribe` | Web Push 구독 해제 |
| | GET | `/push/status` | 구독 상태 확인 |
| | GET | `/push/vapid-key` | VAPID 공개키 조회 |
| **Statistics** | GET | `/cases/statistics/?by=` | 통계 (assignee/status/time, 기간/담당자 필터) |

Swagger UI: `http://localhost:8000/docs`

## Testing

```bash
cd backend

# 테스트 DB 생성 (1회)
createdb cs_dashboard_test

# 전체 테스트 실행
python -m pytest tests/ -v

# 커버리지 포함
python -m pytest tests/ --cov=. --cov-report=term-missing
```

**157개 통합 테스트 (93% 커버리지)** — API CRUD, 알림 시나리오, Celery 태스크, 통계, 유사 케이스, 태그 시스템, 크로스 도메인 플로우 검증.

## Project Structure

```
├── backend/
│   ├── main.py                 # FastAPI entry point + CORS
│   ├── models.py               # SQLAlchemy ORM (12 models incl. case_assignees)
│   ├── schemas.py              # Pydantic request/response
│   ├── database.py             # DB session
│   ├── validators.py           # Shared validation logic
│   ├── celery_app.py           # Celery config (Redis broker + Beat schedule)
│   ├── tasks.py                # Async tasks (notifications, similarity, tag learning)
│   ├── seed.py                 # Test data seeder
│   ├── routers/
│   │   ├── auth.py             # JWT login/me/change-password
│   │   ├── admin.py            # User management (ADMIN only)
│   │   ├── cases.py            # CS Case CRUD + similar search + my-progress
│   │   ├── comments.py         # Comments + nested replies (N+1 optimized)
│   │   ├── checklists.py       # Checklist CRUD (author tracking)
│   │   ├── products.py         # Product CRUD + CSV bulk upload
│   │   ├── licenses.py         # License CRUD
│   │   ├── memos.py            # Product/License memos (author name)
│   │   ├── notifications.py    # Notification list/read
│   │   ├── push.py             # Web Push subscription CRUD
│   │   ├── tags.py             # Tag search/suggest API
│   │   └── statistics.py       # Stats with period/assignee filter
│   ├── services/
│   │   ├── statistics.py       # Statistics business logic
│   │   ├── similarity.py       # TF-IDF + tag similarity engine
│   │   ├── tag_service.py      # Tag CRUD + keyword learning
│   │   ├── push.py             # Web Push delivery (pywebpush)
│   │   └── cache.py            # Redis cache layer
│   ├── alembic/                # DB migrations
│   └── tests/                  # Integration tests (157 cases, 93% coverage)
│
└── frontend/
    └── src/
        ├── api/                # Axios API modules
        │   ├── client.js       # Axios instance + 401 interceptor
        │   ├── cases.js        # Case CRUD + statistics + similar + my-progress
        │   ├── push.js         # Web Push subscribe/unsubscribe/status
        │   └── tags.js         # Tag search/suggest
        ├── constants/
        │   ├── roles.js        # User role constants (ROLES, ROLE_LIST)
        │   ├── caseStatus.js   # Case status constants + labels
        │   └── priority.js     # Priority constants
        ├── contexts/
        │   └── AuthContext.jsx  # Auth state + idle timeout
        ├── hooks/              # useDebounce, usePagination, useFetch, useIdleTimeout
        ├── components/
        │   ├── Layout.jsx        # Sidebar + topbar + notifications + push toggle
        │   ├── CaseForm.jsx      # Case create (multi-assignee, org info, tags)
        │   ├── CaseDetail/       # Detail: InfoCard, Comments, Checklists, SimilarCases
        │   ├── TagInput.jsx      # Hashtag chip input with auto-complete
        │   ├── SimilarCasesWidget.jsx  # Similar cases suggestions (debounced)
        │   ├── Spinner.jsx, Pagination.jsx, CaseList.jsx  # Shared (React.memo)
        │   └── utils.js          # Date formatting, status/priority badge helpers
        ├── pages/
        │   ├── LoginPage.jsx     # Login form
        │   ├── Dashboard.jsx     # Orchestrator (AdminOverview, MyProgress, CaseSection)
        │   ├── dashboard/        # Dashboard sub-components
        │   │   ├── AdminOverview.jsx   # Admin stats + assignee table
        │   │   ├── MyProgress.jsx      # User progress cards
        │   │   └── CaseSection.jsx     # Reusable paginated case list
        │   ├── CasePage.jsx      # Case list with filters
        │   ├── ProductPage.jsx   # Product detail with inline license memos
        │   └── admin/            # ADMIN only pages
        ├── App.jsx             # Router config + code splitting (React.lazy)
        └── main.jsx            # Entry point + AuthProvider
```

## Key Features

- **인증 시스템**: JWT 로그인, 60분 비활동 자동 로그아웃, 역할 기반 접근 제어
- **회원 관리** (ADMIN): 사용자 생성/수정/비활성화, 비밀번호 재설정
- **케이스 관리**: 생성, 조회, 수정, 삭제(cascade), 상태 변경 (OPEN → IN_PROGRESS → DONE / CANCEL), 완료·취소 시간 자동 기록
- **조직 정보**: 케이스별 요청 조직명, 연락처, 담당자 기록
- **복수 담당자 지원**: 케이스당 여러 명의 담당자 배정 가능 (다대다 관계), 모든 담당자에게 알림 발송
- **케이스 생성 자동화**: 요청자(requester)는 로그인 사용자로 자동 설정
- **제품·라이선스 관리**: 제품/라이선스 CRUD (ADMIN), 인라인 라이선스 상세·메모 표시, 메모 작성자 이름 표시
- **CSV 일괄 업로드**: Product + License 대량 등록 (중복 자동 처리)
- **태그 시스템**: 해시태그 입력, 자동 완성, 키워드 기반 추천, Celery 비동기 학습
- **AI 유사 케이스 추천**: TF-IDF + 태그 유사도 결합 (가중치: 태그 50%, 제목 30%, 내용 20%), Redis 캐시
- **댓글 & 체크리스트**: 내부/외부 댓글, 중첩 답글, 댓글 삭제, 체크리스트 작성자 추적
- **알림 시스템**: 복수 담당자 배정 알림, 댓글/답글 알림, 24시간 미처리 리마인드
- **Web Push 알림**: VAPID 기반 OS 알림 + 30초 폴링 fallback (FCM 불안정 우회)
- **업무 통계**: 담당자별/상태별 케이스 현황, 기간 필터 (daily/weekly/monthly), 담당자 필터
- **Dashboard**: My Progress (전체+일별), 내 할당/작성/최근 케이스 (섹션별 페이지네이션)
- **Admin Overview**: 전체 현황 카드 (Total/Open/In Progress/Done/Cancel), 담당자별 업무 현황 테이블, 기간·담당자 필터
- **Dashboard 카드 클릭**: 상태별 케이스 필터링 → CasePage 이동

## Changelog

### v1.5.0 (2026-02-12)
- **CANCEL 상태 추가**: 케이스 취소 상태 + canceled_at 자동 기록
- **조직 정보 필드**: organization, org_phone, org_contact 추가 (CaseForm, InfoCard)
- **체크리스트 작성자 추적**: author_id 필드 추가, 작성자 이름 표시
- **Dashboard 분리**: Dashboard.jsx (327줄 → 38줄) → AdminOverview, MyProgress, CaseSection 서브 컴포넌트
- **My Progress**: 사용자별 케이스 현황 카드 (전체+일별), 날짜 필터
- **Admin Overview 강화**: 기간 필터 (daily/weekly/monthly) + 담당자 필터 드롭다운
- **Backend 클린코드**: similarity 중복 제거 (find_similar_cases 통합), 알림 헬퍼 (_create_and_push), comments N+1 수정
- **Frontend 클린코드**: caseStatus/priority 상수 파일, React.memo (Spinner, CaseList, Pagination), error handling 통일, formatDateShort 통합
- **Statistics 기간 필터**: stat_by_assignee, stat_by_status에 period/targetDate/assigneeId 파라미터 추가

### v1.4.0 (2026-02-10)
- **태그 시스템**: TagMaster 모델, 해시태그 입력 (TagInput), 자동 완성/추천, Celery 비동기 학습
- **TF-IDF 유사도 엔진**: CaseSimilarityEngine, 배치 코사인 유사도, Redis 모델 캐시
- **유사 케이스 추천**: 가중치 결합 (태그 50% + 제목 30% + 내용 20%), 임계값 0.3
- **SimilarCasesWidget**: 케이스 작성 시 실시간 유사 케이스 제안 (debounced)
- **SimilarCasesPanel**: 케이스 상세 사이드바 유사 케이스 패널
- **Celery Beat 태스크**: rebuild_tfidf_model (일간), cleanup_tag_keywords (주간)
- **테스트 확장**: 115개 → 157개 테스트, 커버리지 92% → 93%

### v1.3.0 (2026-02-06)
- **Web Push 알림**: VAPID 기반 OS 푸시 알림 (pywebpush + FCM)
- **HTTPS 개발 환경**: mkcert 인증서 + Vite HTTPS proxy 구성
- **폴링 기반 OS 알림 Fallback**: FCM 전달 불안정 우회, 30초 폴링으로 OS Notification 표시
- **PushSubscription 모델**: endpoint, p256dh, auth 저장
- **Service Worker**: push/notificationclick 이벤트 핸들러 (sw.js)
- **Push 토글 UI**: Layout.jsx에 구독/해제 토글 버튼

### v1.2.0 (2026-02-04)
- **Static Analysis 전체 수행**: 26개 항목 점검 완료 (5 Phase)
- **Backend 구조 개선**: dead code 제거, statistics 서비스 분리, validation 통합, Celery M2M 알림 수정
- **Backend 보안 강화**: 전 엔드포인트 인증 적용, CSV 업로드 크기/행수 제한, 에러 메시지 영문 통일
- **Backend 테스트**: 87개 → 115개 테스트, 커버리지 55% → 92%, 전 엔드포인트 docstring 추가
- **Frontend 컴포넌트 분리**: ProductDetailCard, LicenseListCard, ProductSearchDropdown, SimilarCasesWidget, Spinner
- **Frontend 품질 개선**: role 상수 중앙화, CSS 모듈 분리, error handling 통일, a11y 개선
- **Frontend 성능**: React.lazy 코드 스플리팅, React.memo/useCallback 적용, JWT 만료 클라이언트 체크
- **개발 규칙 수립**: CLAUDE.md에 Backend/Frontend 코딩 규칙 추가

### v1.1.0 (2026-02-03)
- **Products 페이지 개선**: 라이선스 인라인 상세 표시, 별도 라이선스 페이지 제거
- **메모 작성자 표시**: ProductMemo/LicenseMemo에 작성자 이름 표시
- **Case Requester 자동 설정**: 로그인 사용자 이름으로 자동 설정 (읽기 전용)
- **복수 Assignee 지원**: case_assignees 다대다 테이블, 복수 담당자 선택 UI, 통계/알림 연동
- **Dashboard 개선**: My Assigned Cases, My Created Cases 섹션 추가, ADMIN 전용 업무 현황

### v1.0.6 (2025)
- Dashboard 상태 카드 클릭 필터링, 422 에러 수정

### v1.0.5 (2025)
- Case 상세 담당자 이름 표시, 완료 시간, 댓글 삭제

### v1.0.4 (2025)
- Product/License/Memo 전체 CRUD

### v1.0.3 (2025)
- CS Case 기능 업그레이드

### v1.0.2 (2025)
- 인증 시스템, 프론트엔드 모듈화

## License

Internal use only.
