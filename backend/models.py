import enum
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from database import Base


# ---------- Enums ----------

class UserRole(str, enum.Enum):
    CS = "CS"
    ENGINEER = "ENGINEER"
    ADMIN = "ADMIN"


class CaseStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCEL = "CANCEL"


class Priority(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class QuoteRequestStatus(str, enum.Enum):
    OPEN = "OPEN"
    DONE = "DONE"


class NotificationType(str, enum.Enum):
    ASSIGNEE = "ASSIGNEE"
    REMINDER = "REMINDER"
    COMMENT = "COMMENT"


# ---------- Models ----------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.CS, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_quote_assignee = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    assigned_cases = relationship("CSCase", back_populates="assignee")
    notifications = relationship("Notification", back_populates="user")
    push_subscriptions = relationship(
        "PushSubscription", back_populates="user", cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("User")
    licenses = relationship("License", back_populates="product")
    memos = relationship("ProductMemo", back_populates="product")


class License(Base):
    __tablename__ = "licenses"
    __table_args__ = (
        UniqueConstraint("product_id", "name", name="uq_licenses_product_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="licenses")
    memos = relationship("LicenseMemo", back_populates="license")


class ProductMemo(Base):
    __tablename__ = "product_memos"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="memos")
    author = relationship("User")

    @property
    def author_name(self):
        return self.author.name if self.author else None


class LicenseMemo(Base):
    __tablename__ = "license_memos"

    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, ForeignKey("licenses.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    license = relationship("License", back_populates="memos")
    author = relationship("User")

    @property
    def author_name(self):
        return self.author.name if self.author else None


case_assignees = Table(
    "case_assignees",
    Base.metadata,
    Column("case_id", Integer, ForeignKey("cs_cases.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class CSCase(Base):
    __tablename__ = "cs_cases"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"))
    license_id = Column(Integer, ForeignKey("licenses.id"))
    requester = Column(String, nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"))
    status = Column(SQLEnum(CaseStatus), default=CaseStatus.OPEN, nullable=False)
    priority = Column(SQLEnum(Priority), default=Priority.MEDIUM, nullable=False)
    tags = Column(ARRAY(String), default=[])
    organization = Column(String, nullable=True)
    org_phone = Column(String, nullable=True)
    org_contact = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    canceled_at = Column(DateTime, nullable=True)

    assignee = relationship("User", back_populates="assigned_cases")
    assignees = relationship("User", secondary=case_assignees, backref="multi_assigned_cases")
    product = relationship("Product")
    license = relationship("License")
    comments = relationship("Comment", back_populates="case", cascade="all, delete-orphan")
    checklists = relationship("Checklist", back_populates="case", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="case", cascade="all, delete-orphan")

    @property
    def assignee_ids(self):
        return [u.id for u in self.assignees] if self.assignees else []

    @property
    def assignee_names(self):
        return [u.name for u in self.assignees] if self.assignees else []


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cs_cases.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CSCase", back_populates="comments")
    author = relationship("User")
    parent = relationship("Comment", remote_side=[id], back_populates="replies")
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")


class Checklist(Base):
    __tablename__ = "checklists"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cs_cases.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    content = Column(String, nullable=False)
    is_done = Column(Boolean, default=False)

    case = relationship("CSCase", back_populates="checklists")
    author = relationship("User")

    @property
    def author_name(self):
        return self.author.name if self.author else None


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("cs_cases.id"), nullable=True)
    quote_request_id = Column(Integer, ForeignKey("quote_requests.id"), nullable=True)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    type = Column(SQLEnum(NotificationType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")
    case = relationship("CSCase", back_populates="notifications")
    quote_request = relationship("QuoteRequest")


class PushSubscription(Base):
    """Browser Web Push subscription per user device."""

    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    endpoint = Column(String, unique=True, nullable=False)
    p256dh = Column(String, nullable=False)
    auth = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="push_subscriptions")


class TagMaster(Base):
    """Tag registry for auto-complete, suggestions, and keyword learning."""

    __tablename__ = "tag_master"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    usage_count = Column(Integer, default=0)
    keyword_weights = Column(JSONB, default={})
    created_by = Column(String, default="user")  # "user" | "system" | "seed"
    created_at = Column(DateTime, default=func.now())


# ---------- Quote Request ----------

quote_request_assignees = Table(
    "quote_request_assignees",
    Base.metadata,
    Column("quote_request_id", Integer, ForeignKey("quote_requests.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class QuoteRequest(Base):
    __tablename__ = "quote_requests"

    id = Column(Integer, primary_key=True, index=True)
    # Incoming data fields
    received_at = Column(DateTime, nullable=False)
    delivery_date = Column(String, nullable=True)
    email_id = Column(String, nullable=True)
    email = Column(String, nullable=True)
    organization = Column(String, nullable=True)
    quote_request = Column(Text, nullable=False)
    other_request = Column(Text, nullable=True)
    failed_products = Column(JSONB, nullable=True)
    additional_request = Column(Text, nullable=True)
    # System fields
    status = Column(SQLEnum(QuoteRequestStatus), default=QuoteRequestStatus.OPEN, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    # Relationships
    assignees = relationship("User", secondary=quote_request_assignees)
    comments = relationship("QuoteRequestComment", back_populates="quote_request", cascade="all, delete-orphan")

    @property
    def assignee_ids(self):
        return [u.id for u in self.assignees] if self.assignees else []

    @property
    def assignee_names(self):
        return [u.name for u in self.assignees] if self.assignees else []


class QuoteRequestComment(Base):
    __tablename__ = "quote_request_comments"

    id = Column(Integer, primary_key=True, index=True)
    quote_request_id = Column(Integer, ForeignKey("quote_requests.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("quote_request_comments.id"), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    quote_request = relationship("QuoteRequest", back_populates="comments")
    author = relationship("User")
    parent = relationship("QuoteRequestComment", remote_side=[id], back_populates="replies")
    replies = relationship("QuoteRequestComment", back_populates="parent", cascade="all, delete-orphan")
