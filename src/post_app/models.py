from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey, Date, Integer, String, Boolean, Text, Enum as SAEnum, UUID
import uuid
from src.db.base import Base
from datetime import datetime, timedelta, timezone, UTC, date
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.accounts.models import User

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