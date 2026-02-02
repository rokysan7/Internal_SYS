"""
FastAPI 앱 엔트리포인트.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import admin, auth, cases, checklists, comments, licenses, memos, notifications, products, statistics

app = FastAPI(title="CS Dashboard API", version="1.0.4")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용 (내부망 사용)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(products.router)
app.include_router(licenses.router)
app.include_router(memos.router)
app.include_router(cases.router)
app.include_router(comments.router)
app.include_router(checklists.router)
app.include_router(notifications.router)
app.include_router(statistics.router)


@app.get("/")
def root():
    return {"message": "CS Dashboard API"}
