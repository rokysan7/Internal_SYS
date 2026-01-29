# CS Case Management Dashboard

> **Version**: Backend v1.0.2 / Frontend v1.0.2

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
│  (Vite)     │   Bearer JWT      │  10 Routers   │              │  8 Tables  │
└─────────────┘                   └──────┬───────┘              └────────────┘
                                         │ .delay()
                                         ▼
                                  ┌──────────────┐
                                  │ Celery Worker │ ←── Redis Broker
                                  │ + Beat        │
                                  └──────────────┘
```

### Database Schema (8 Tables)

- **User** — 역할: CS / ENGINEER / ADMIN
- **Product** → has many **License**
- **ProductMemo** / **LicenseMemo** — 제품·라이선스별 지식 축적
- **CSCase** → belongs to Product, License, User(assignee)
- **Comment** — 내부/외부 구분 (`is_internal`)
- **Checklist** — 케이스별 체크리스트
- **Notification** — ASSIGNEE / REMINDER / COMMENT 타입

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
| **Licenses** | POST | `/licenses/` | 라이선스 생성 |
| | GET | `/licenses/{id}` | 라이선스 상세 |
| **Memos** | GET/POST | `/products/{id}/memos` | 제품 메모 |
| | GET/POST | `/licenses/{id}/memos` | 라이선스 메모 |
| **Cases** | GET | `/cases/` | 케이스 목록 (status, assignee, product 필터) |
| | POST | `/cases/` | 케이스 생성 |
| | GET | `/cases/{id}` | 케이스 상세 |
| | PUT | `/cases/{id}` | 케이스 수정 |
| | PATCH | `/cases/{id}/status` | 상태 변경 |
| | GET | `/cases/similar?query=` | 유사 케이스 검색 |
| **Comments** | GET/POST | `/cases/{id}/comments` | 댓글 CRUD |
| **Checklists** | GET/POST | `/cases/{id}/checklists` | 체크리스트 CRUD |
| | PATCH | `/checklists/{id}` | 체크리스트 토글 |
| **Notifications** | GET | `/notifications/` | 알림 목록 (user_id, unread 필터) |
| | PATCH | `/notifications/{id}/read` | 읽음 처리 |
| **Statistics** | GET | `/cases/statistics/?by=` | 통계 (assignee/status/time) |

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

**82개 통합 테스트** — API CRUD, 알림 시나리오, Celery 태스크, 통계, 크로스 도메인 플로우 검증.

## Project Structure

```
├── backend/
│   ├── main.py                 # FastAPI entry point + CORS
│   ├── models.py               # SQLAlchemy ORM (8 models)
│   ├── schemas.py              # Pydantic request/response
│   ├── database.py             # DB session
│   ├── celery_app.py           # Celery config (Redis broker)
│   ├── tasks.py                # Async tasks (reminder, comment notify)
│   ├── seed.py                 # Test data seeder
│   ├── routers/
│   │   ├── auth.py             # JWT login/me/change-password
│   │   ├── admin.py            # User management (ADMIN only)
│   │   ├── cases.py            # CS Case CRUD + similar search
│   │   ├── comments.py         # Comments + Celery trigger
│   │   ├── checklists.py       # Checklist CRUD
│   │   ├── products.py         # Product CRUD
│   │   ├── licenses.py         # License CRUD
│   │   ├── memos.py            # Product/License memos
│   │   ├── notifications.py    # Notification list/read
│   │   └── statistics.py       # Assignee/status/time stats
│   ├── alembic/                # DB migrations
│   └── tests/                  # Integration tests (82 cases)
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_products.py
│       ├── test_licenses.py
│       ├── test_cases.py
│       ├── test_comments.py
│       ├── test_checklists.py
│       ├── test_notifications.py
│       ├── test_statistics.py
│       ├── test_celery_tasks.py
│       └── test_integration_flows.py
│
└── frontend/
    └── src/
        ├── api/                # Axios API modules
        │   ├── client.js       # Axios instance + 401 interceptor
        │   ├── auth.js         # login, me, changePassword
        │   └── admin.js        # User management API
        ├── contexts/
        │   └── AuthContext.jsx # Auth state + idle timeout
        ├── hooks/
        │   └── useIdleTimeout.js # Idle detection hook
        ├── components/
        │   ├── PrivateRoute.jsx  # Login required wrapper
        │   ├── AdminRoute.jsx    # ADMIN role required wrapper
        │   ├── Layout.jsx        # Sidebar + topbar + user info
        │   ├── Pagination.jsx, SortButtons.jsx, etc.
        ├── pages/
        │   ├── LoginPage.jsx     # Login form
        │   ├── admin/            # ADMIN only pages
        │   │   ├── UserListPage.jsx
        │   │   ├── UserCreatePage.jsx
        │   │   └── UserEditPage.jsx
        │   └── Dashboard, CasePage, ProductPage, LicensePage
        ├── App.jsx             # Router config + route protection
        └── main.jsx            # Entry point + AuthProvider
```

## Key Features

- **인증 시스템**: JWT 로그인, 60분 비활동 자동 로그아웃, 역할 기반 접근 제어
- **회원 관리** (ADMIN): 사용자 생성/수정/비활성화, 비밀번호 재설정
- **케이스 관리**: 생성, 조회, 수정, 상태 변경 (OPEN → IN_PROGRESS → DONE)
- **제품·라이선스 연동**: 제품별 라이선스 관리 및 메모 축적
- **CSV 일괄 업로드**: Product + License 대량 등록 (중복 자동 처리)
- **페이지네이션 & 정렬**: 제품 목록 25개 단위 페이징, 이름/날짜순 정렬
- **댓글 & 체크리스트**: 내부/외부 댓글, 케이스별 체크리스트
- **알림 시스템**: 담당자 배정, 댓글, 24시간 미처리 리마인드 (Celery 비동기)
- **AI 유사 케이스 추천**: 제목/내용 기반 과거 케이스 검색
- **업무 통계**: 담당자별/상태별 케이스 현황, 평균 처리 시간
- **30초 폴링 알림 Badge**: 실시간에 준하는 미읽음 알림 표시

## License

Internal use only.
