
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey, Date, Integer, String, Boolean, Text, Enum as SAEnum, UUID
import uuid
from src.db.base import Base
from datetime import datetime, timedelta, timezone, UTC, date
from enum import Enum

class UserRole(Enum):
    admin = 'admin'
    user = 'user'
    staff = 'staff'

class User(Base):
    __tablename__ = "account_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, index=True, default=uuid.uuid4, nullable=False)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    user_role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="user_role_enum"), default=UserRole.user)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    image_file: Mapped[str | None] = mapped_column(
        String(400),
        nullable=True, default=None
    )

    @property
    def image_path(self):
        if self.image_file:
            return f'/media/profile_pics/{self.image_file}'
        return f'/static/profile_pics/default.jpg'
    
    posts: Mapped[list['Post']] = relationship(
        back_populates='author',
        lazy='raise',
        cascade='all, delete-orphan'
        )
    
    def __repr__(self):
        return f"<User (id: {self.id}), (email: {self.email})>"
    
class Post(Base):
    __tablename__ = 'account_posts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "account_users.key", 
            # ondelete='CASCADE'
            ), 
            nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str]  = mapped_column(Text, nullable=False)
    date_posted: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    author: Mapped['User'] = relationship(back_populates='posts', lazy="raise")