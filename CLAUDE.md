# CLAUDE.md

Guidance for Claude Code when working with this repository.

## Project Overview

Internal CS (Customer Support) Case Management System.
- **Frontend**: React + Vite + Axios + React Router
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Async Tasks**: Celery + Redis

## Current Phase

**Status**: v1.6.0 Quote Requests + Security Hardening

**Workflow**: Checklist-driven development. Each feature or refactoring task has its own checklist file.

## Active Checklists

None — all checklists completed.

## Code Rules

### General
- **Line limit**: Each file must not exceed **650 lines**. Split into submodules if approaching limit.
- **Modularization**: Maximize reusability by splitting code into purpose-driven modules (components, hooks, utilities).
- **Reusability check**: Before writing new code, always check if existing reusable modules can be used. When creating new code, evaluate if it should be a reusable module.
- **Single responsibility**: Each file/function should have one clear purpose. Do not mix CRUD, business logic, and notification in one file.
- **Git**: Never run `git add`, `git commit`, `git push` unless explicitly requested by user.
- **Package manager**: Use `uv` instead of pip for Python dependencies.
- **Auto-update**: When creating new reusable modules, always update the "Reusable Modules" section below.
- **Language**: Use English only in CLAUDE.md files.

### Backend Rules
- **Auth required**: Every data endpoint (GET/POST/PUT/DELETE) MUST include `Depends(get_current_user)`. Use `require_role()` for admin-only operations.
- **Enum over magic strings**: Always use model Enums (`UserRole.ADMIN`, `CaseStatus.DONE`, `Priority.HIGH`). Never compare with raw strings like `"DONE"` or `"ADMIN"`.
- **Error messages in English**: All `HTTPException` detail messages must be in English. No Korean in API responses.
- **Validation in one place**: Shared validation logic (password rules, etc.) goes in `validators.py`. Never duplicate validation across routers.
- **Async notifications via Celery**: All notification creation must go through Celery tasks (`tasks.py`). Never insert `Notification` records synchronously inside request handlers.
- **M2M relationships**: Use `case.assignees` (many-to-many list), not `case.assignee_id`. Always iterate over the full assignee list when sending notifications.
- **No N+1 queries**: Use `joinedload()` for eager loading relationships. Use `GROUP BY` aggregate queries instead of Python loops with per-item queries.
- **Docstrings on all endpoints**: Every router function must have a docstring. FastAPI uses it for Swagger UI auto-documentation.
- **CSV/file upload limits**: Always enforce file size limit (5MB) and row count limit (10,000) on bulk upload endpoints.
- **Import order**: Follow `stdlib → third-party → local` order. Remove unused imports.
- **Business logic in services/**: Extract complex business logic (statistics, aggregations) into `services/` directory. Routers should only handle HTTP concerns.

### Frontend Rules
- **Use role constants**: Always use `ROLES.ADMIN`, `ROLES.CS`, `ROLES.ENGINEER` from `src/constants/roles.js`. Never hardcode role strings like `'ADMIN'`.
- **Component size limit**: If a component has more than 8 `useState` hooks, split it into sub-components. Each sub-component should manage its own state.
- **Consistent error handling**: All API `.catch()` blocks must show user feedback via `alert()` or toast. Never use `console.error()` alone — the user must see the error.
- **Loading state**: Use the shared `<Spinner />` component for all loading states. Do not use raw `<div>Loading...</div>` text.
- **Code splitting**: All page components in `App.jsx` must use `React.lazy()` + `<Suspense>`. Only import shared components (Layout, PrivateRoute, AdminRoute) statically.
- **Performance**: Apply `React.memo` to reusable components that receive stable props. Use `useCallback` for event handlers passed as props to memoized children.
- **ARIA on custom widgets**: Custom dropdowns, modals, and interactive elements must include `role`, `aria-expanded`, `aria-label` attributes and keyboard navigation support.
- **CSS organization**: Keep CSS split by concern (base, card, form, component). Do not pile unrelated styles into a single file beyond 300 lines.
- **Token management**: `client.js` Axios interceptor handles token attachment and 401 auto-logout. Client-side JWT expiry check is implemented — maintain this pattern for new auth flows.

## Reusable Modules

### Frontend Components (`src/components/`)
| Component | Purpose | Usage |
|-----------|---------|-------|
| `Pagination.jsx` | Pagination UI | List pages |
| `SortButtons.jsx` | Sort buttons (name/date) | List pages |
| `Spinner.jsx` | Loading spinner with text | All loading states |
| `MemoList.jsx` | Memo list/form | Product, License detail |
| `ProductDetailCard.jsx` | Product detail view with inline edit | ProductPage |
| `LicenseListCard.jsx` | License table with selection/delete | ProductPage |
| `ProductSearchDropdown.jsx` | Searchable product dropdown | CaseForm |
| `SimilarCasesWidget.jsx` | Similar cases suggestions with score, tags, status (debounced) | CaseForm |
| `CaseDetail/SimilarCasesPanel.jsx` | Similar cases panel for case detail sidebar | CaseDetail |
| `TagInput.jsx` | Hashtag chip input with auto-complete and suggestions | CaseForm |
| `PrivateRoute.jsx` | Auth-required route wrapper | App.jsx |
| `AdminRoute.jsx` | Admin-only route wrapper | App.jsx |
| `Layout.jsx` | Common layout (sidebar, topbar, notifications, push toggle) | App.jsx |
| `utils.js` | Date formatting (formatDate, formatDateShort), status/priority badge helpers | CaseList, MemoList, SimilarCasesWidget, UserListPage |

### Frontend Dashboard Sub-components (`src/pages/dashboard/`)
| Component | Purpose | Usage |
|-----------|---------|-------|
| `AdminOverview.jsx` | Admin status cards + assignee stats table (period/assignee filter) | Dashboard |
| `MyProgress.jsx` | Current user's case counts (all-time + date-filtered) | Dashboard |
| `CaseSection.jsx` | Paginated case list section (reusable) | Dashboard |

### Frontend API (`src/api/`)
| Module | Purpose | Usage |
|--------|---------|-------|
| `push.js` | Web Push subscribe/unsubscribe/status utilities | Layout.jsx |
| `tags.js` | Tag search/suggest API utilities | TagInput.jsx |

### Frontend Constants (`src/constants/`)
| Module | Purpose | Usage |
|--------|---------|-------|
| `roles.js` | User role constants (ROLES, ROLE_LIST) | All role checks, admin pages |
| `caseStatus.js` | Case status constants (CASE_STATUS, CASE_STATUS_LIST, CASE_STATUS_LABEL) | Status checks, badges, filters |
| `priority.js` | Priority constants (PRIORITY, PRIORITY_LIST) | Priority checks, badges, filters |

### Frontend Hooks (`src/hooks/`)
| Hook | Purpose | Usage |
|------|---------|-------|
| `useDebounce.js` | Input debounce | Search fields |
| `usePagination.js` | Pagination state management | List pages |
| `useFetch.js` | API call + loading/error state | Data fetching |
| `useIdleTimeout.js` | Idle detection | Auto logout |

### Backend Utilities
| Module | Purpose | Usage |
|--------|---------|-------|
| `routers/auth.py:get_current_user` | JWT auth dependency | All auth-required endpoints |
| `routers/auth.py:require_role()` | Role-based access control | Admin-only endpoints |
| `validators.py` | Common validation (password, etc.) | admin.py, auth.py |
| `services/statistics.py` | Case statistics business logic | cases.py |
| `services/push.py:send_push_to_user` | Web Push delivery to user devices | tasks.py |
| `routers/push.py` | Push subscription CRUD endpoints | Layout.jsx (frontend) |
| `tasks.py:notify_case_assigned` | Async assignee notification (Celery) | cases.py |
| `tasks.py:notify_comment` | Async comment notification (Celery) | comments.py |
| `tasks.py:notify_reply` | Async reply notification (Celery) | comments.py |
| `tasks.py:check_pending_cases` | Periodic reminder for stale cases (Celery Beat) | celery_app.py |
| `tasks.py:learn_tags_from_case` | Async tag keyword learning (Celery) | cases.py |
| `services/similarity.py:extract_keywords` | Korean keyword extraction (kiwipiepy) | tag_service.py, similarity engine |
| `services/similarity.py:CaseSimilarityEngine` | TF-IDF similarity engine (fit, vectorize, batch cosine similarity) | tasks.py, cases.py |
| `services/similarity.py:SIMILARITY_THRESHOLD` | Env-configurable similarity threshold (default 0.3) | tasks.py, cases.py |
| `services/similarity.py:compute_tag_similarity` | Jaccard tag similarity | tasks.py, cases.py |
| `services/similarity.py:compute_combined_similarity` | Weighted similarity (tag 50% + title 30% + content 20%) | tasks.py, cases.py |
| `services/similarity.py:find_similar_cases` | Unified similar case finder (TF-IDF + tag, top-N) | cases.py, tasks.py |
| `tasks.py:_create_and_push` | Common notification creation + push helper | notify_comment, notify_case_assigned, notify_reply |
| `services/cache.py` | Redis DB 2 cache layer (similar cases, TF-IDF model) | tasks.py, cases.py, similarity.py |
| `services/tag_service.py` | Tag CRUD, keyword learning, suggestions | tags.py, tasks.py |
| `routers/tags.py` | Tag search/suggest API endpoints | TagInput.jsx (frontend) |
| `tasks.py:cleanup_tag_keywords` | Weekly tag keyword cleanup (Celery Beat) | celery_app.py |
| `tasks.py:compute_case_similarity` | Async case similarity computation (batch optimized) | cases.py |
| `tasks.py:rebuild_tfidf_model` | Daily TF-IDF model rebuild (batch optimized, Celery Beat) | celery_app.py |

### Test Fixtures (`tests/conftest.py`)
| Fixture | Purpose | Usage |
|---------|---------|-------|
| `client` | Authenticated TestClient (ADMIN role, DB override) | All API tests |
| `unauth_client` | Unauthenticated TestClient (DB only) | Auth flow tests |
| `celery_eager` | Runs Celery tasks synchronously in test session | Auto-applied to all tests |
| `sample_case` | Pre-created case with assignee, product, license | Case-dependent tests |
| `sample_tags` | 5 seed TagMaster entries with keyword_weights | Tag search/suggest tests |
| `sample_cases_for_similarity` | 3 cases with overlapping tags/titles | Similarity API tests |

## Commands

### Backend
```bash
# Dev server (use --host 0.0.0.0 for external IP access)
uvicorn main:app --reload --port 8002 --host 0.0.0.0

# Celery worker (requires Redis)
celery -A celery_app worker --loglevel=info

# Celery beat
celery -A celery_app beat --loglevel=info

# DB migration
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### Testing
```bash
cd backend
source .venv/bin/activate
pytest tests/ -v                    # Run all tests
pytest tests/ --cov=. --cov-report=term-missing  # With coverage
pytest tests/test_cases.py -v       # Single test file
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # Dev server
npm run build    # Production build
```

### Python Environment (uv)
```bash
uv venv
source .venv/bin/activate
uv add <package>
```

## Architecture Summary

### Backend Structure
```
backend/
├── main.py          # FastAPI entry
├── models.py        # SQLAlchemy models
├── database.py      # DB session
├── schemas.py       # Pydantic schemas
├── validators.py    # Shared validation logic
├── routers/         # API routes (auth, admin, cases, products, licenses, etc.)
├── services/        # Business logic (statistics.py, push.py)
├── celery_app.py    # Celery config
├── tasks.py         # Async tasks (notifications, reminders, web push)
└── tests/           # Pytest suite (157 tests, 93% coverage)
```

### Frontend Structure
```
frontend/src/
├── api/             # Axios API modules (client.js, push.js)
├── components/      # Reusable UI components (React.memo optimized)
├── constants/       # Shared constants (roles.js)
├── contexts/        # React Context providers (auth, etc.)
├── hooks/           # Custom React hooks
├── pages/           # Page components (React.lazy code-split)
├── App.jsx          # Routes with Suspense + lazy loading
└── main.jsx
```

### Database (12 tables)
User, Product, License, ProductMemo, LicenseMemo, CSCase, case_assignees, Comment, Checklist, Notification, PushSubscription, TagMaster

### Key Enums
- `UserRole`: CS, ENGINEER, ADMIN
- `CaseStatus`: OPEN, IN_PROGRESS, DONE, CANCEL
- `Priority`: HIGH, MEDIUM, LOW
