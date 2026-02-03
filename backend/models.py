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
)
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


class Priority(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


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
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    assigned_cases = relationship("CSCase", back_populates="assignee")
    notifications = relationship("Notification", back_populates="user")


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
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

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
    content = Column(String, nullable=False)
    is_done = Column(Boolean, default=False)

    case = relationship("CSCase", back_populates="checklists")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("cs_cases.id"), nullable=True)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    type = Column(SQLEnum(NotificationType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")
    case = relationship("CSCase", back_populates="notifications")
