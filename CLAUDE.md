# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Internal CS (Customer Support) Case Management System built with **React (Frontend)** + **FastAPI/Python (Backend)**. The system manages CS cases, products, licenses, notifications, and work statistics for internal operations.

All design documents and code skeletons are in `Guide_and_Instruction/`.

## Code Line Limit

**Each file must not exceed 650 lines of code.** If a file approaches this limit, split it into logical submodules.

## Architecture

### Backend (FastAPI + SQLAlchemy + PostgreSQL)

```
backend/
├── main.py              # FastAPI app entry point
├── models.py            # SQLAlchemy ORM models (User, Product, License, CSCase, etc.)
├── database.py          # DB session setup
├── routers/             # API route modules
│   ├── auth.py
│   ├── cases.py
│   ├── products.py
│   ├── licenses.py
│   ├── memos.py
│   ├── comments.py
│   ├── checklists.py
│   ├── notifications.py
│   └── statistics.py
├── celery_app.py        # Celery config (Redis broker)
└── tasks.py             # Async tasks (reminder, comment notification)
```

### Frontend (React + Axios + React Router)

```
frontend/src/
├── api/                 # Axios API call modules
│   ├── cases.js
│   ├── products.js
│   ├── licenses.js
│   ├── memos.js
│   └── notifications.js
├── components/          # Reusable UI components
│   ├── CaseList.jsx
│   ├── CaseDetail.jsx
│   ├── CaseForm.jsx
│   ├── ProductSearch.jsx
│   ├── LicenseDetail.jsx
│   └── MemoList.jsx
├── pages/               # Page-level components
│   ├── Dashboard.jsx
│   ├── CasePage.jsx
│   ├── ProductPage.jsx
│   └── LicensePage.jsx
├── App.jsx
└── index.js
```

### Database Schema (8 tables)

- **User** (roles: CS / ENGINEER / ADMIN)
- **Product** → has many **License**
- **ProductMemo** / **LicenseMemo** (knowledge accumulation)
- **CSCase** → belongs to Product + License, has **Comment**, **Checklist**
- **Notification** (types: ASSIGNEE / REMINDER / COMMENT)

### Key Enums

- `UserRole`: CS, ENGINEER, ADMIN
- `CaseStatus`: OPEN, IN_PROGRESS, DONE
- `Priority`: HIGH, MEDIUM, LOW
- `NotificationType`: ASSIGNEE, REMINDER, COMMENT

## API Endpoints

| Domain | Endpoints |
|--------|-----------|
| Auth | `POST /auth/login`, `GET /auth/me` |
| Products | `GET/POST /products`, `GET /products/{id}`, `GET /products/{id}/licenses` |
| Licenses | `POST /licenses`, `GET /licenses/{id}` |
| Memos | `GET/POST /products/{id}/memos`, `GET/POST /licenses/{id}/memos` |
| CS Cases | `GET/POST /cases`, `GET/PUT /cases/{id}`, `PATCH /cases/{id}/status`, `GET /cases/similar` |
| Comments | `GET/POST /cases/{id}/comments` |
| Checklists | `GET/POST /cases/{id}/checklists`, `PATCH /checklists/{id}` |
| Notifications | `GET /notifications`, `PATCH /notifications/{id}/read` |
| Statistics | `GET /cases/statistics?by=assignee\|status\|time` |

## Backend Commands

```bash
# Run FastAPI dev server
uvicorn main:app --reload --port 8000

# Run Celery worker (requires Redis)
celery -A celery_app worker --loglevel=info

# Run Celery beat (periodic tasks)
celery -A celery_app beat --loglevel=info

# DB migration (Alembic)
alembic upgrade head
alembic revision --autogenerate -m "description"
```

## Frontend Commands

```bash
# Install dependencies
npm install

# Dev server
npm start

# Build
npm run build
```

## Key Design Decisions

- **Product/License separation**: Products contain multiple Licenses; each has its own memo system for knowledge accumulation
- **Async notifications**: Celery + Redis handles comment notifications and pending case reminders (24h threshold)
- **AI recommendation**: `/cases/similar` endpoint for suggesting similar past cases based on title/content
- **Internal vs public comments**: `Comment.is_internal` flag distinguishes internal memos from customer-facing replies
- **Frontend API base**: All Axios calls target `http://localhost:8000` (configurable via `API_BASE`)
