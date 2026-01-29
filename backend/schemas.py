"""
Pydantic 요청/응답 스키마 정의.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr

from models import CaseStatus, NotificationType, Priority, UserRole


# ======================== User ========================


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.CS


class UserRead(UserBase):
    id: int
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


# ======================== Product ========================


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProductCreate(ProductBase):
    created_by: Optional[int] = None


class ProductRead(ProductBase):
    id: int
    created_by: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    """Product 목록 페이지네이션 응답"""
    items: List[ProductRead]
    total: int
    page: int
    page_size: int
    total_pages: int


# ======================== License ========================


class LicenseBase(BaseModel):
    name: str
    description: Optional[str] = None
    product_id: int


class LicenseCreate(LicenseBase):
    pass


class LicenseRead(LicenseBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ======================== ProductMemo ========================


class ProductMemoBase(BaseModel):
    content: str


class ProductMemoCreate(ProductMemoBase):
    pass


class ProductMemoRead(ProductMemoBase):
    id: int
    product_id: int
    author_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ======================== LicenseMemo ========================


class LicenseMemoBase(BaseModel):
    content: str


class LicenseMemoCreate(LicenseMemoBase):
    pass


class LicenseMemoRead(LicenseMemoBase):
    id: int
    license_id: int
    author_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ======================== CSCase ========================


class CaseBase(BaseModel):
    title: str
    content: str
    product_id: Optional[int] = None
    license_id: Optional[int] = None
    requester: str
    assignee_id: Optional[int] = None
    priority: Priority = Priority.MEDIUM
    tags: Optional[List[str]] = []


class CaseCreate(CaseBase):
    pass


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    product_id: Optional[int] = None
    license_id: Optional[int] = None
    requester: Optional[str] = None
    assignee_id: Optional[int] = None
    priority: Optional[Priority] = None
    tags: Optional[List[str]] = None


class CaseStatusUpdate(BaseModel):
    status: CaseStatus


class CaseRead(CaseBase):
    id: int
    status: CaseStatus
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CaseSimilarRead(BaseModel):
    id: int
    title: str
    status: CaseStatus
    assignee_id: Optional[int] = None

    model_config = {"from_attributes": True}


# ======================== Comment ========================


class CommentBase(BaseModel):
    content: str
    is_internal: bool = False


class CommentCreate(CommentBase):
    pass


class CommentRead(CommentBase):
    id: int
    case_id: int
    author_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ======================== Checklist ========================


class ChecklistBase(BaseModel):
    content: str


class ChecklistCreate(ChecklistBase):
    pass


class ChecklistUpdate(BaseModel):
    is_done: bool


class ChecklistRead(ChecklistBase):
    id: int
    case_id: int
    is_done: bool

    model_config = {"from_attributes": True}


# ======================== Notification ========================


class NotificationRead(BaseModel):
    id: int
    user_id: int
    case_id: Optional[int] = None
    message: str
    is_read: bool
    type: NotificationType
    created_at: datetime

    model_config = {"from_attributes": True}


# ======================== Auth ========================


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ======================== Statistics ========================


class StatByAssignee(BaseModel):
    assignee_id: int
    assignee_name: str
    open_count: int
    in_progress_count: int
    done_count: int


class StatByStatus(BaseModel):
    status: CaseStatus
    count: int


class StatByTime(BaseModel):
    avg_hours: Optional[float] = None
    total_completed: int


# ======================== Bulk Upload ========================


class BulkUploadResult(BaseModel):
    products_created: int
    products_existing: int
    licenses_created: int
    licenses_existing: int
    errors: List[str] = []
