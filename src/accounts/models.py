
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey, Date, Integer, String, Boolean, Text, Enum as SAEnum, UUID
import uuid
from src.config import Config
from src.db.base import Base
from datetime import datetime, timedelta, timezone, UTC, date
from enum import Enum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.post_app.models import Post


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

    # @property
    # def image_path(self):
    #     if self.image_file:
    #         return f'/media/profile_pics/{self.image_file}'
    #     return f'/static/profile_pics/default.jpg'

    @property
    def image_path(self):

        if self.image_file:
            return f"https://{Config.AWS_BUCKET_NAME}.s3.{Config.AWS_REGION}.amazonaws.com/profile_pics/{self.image_file}"
            # https://fastapi-blog-uploads-linus.s3.ap-south-1.amazonaws.com/profile_pics/Screenshot_2026-05-26_17-20-24.png-d042852d-ccec-4735-905b-c118e14fa2a2.png                                    
            # https://fastapi-blog-uploads-linus.s3.ap-south-1.amazonaws.com/profile_pics/c0a8ac5e-caa1-47e0-8bbd-fceabd5f9be9.png
        return "/static/profile_pics/default.jpg"


    
    posts: Mapped[list['Post']] = relationship(
        back_populates='author',
        lazy='raise',
        cascade='all, delete-orphan'
        )
    
    def __repr__(self):
        return f"<User (id: {self.id}), (email: {self.email})>"
    