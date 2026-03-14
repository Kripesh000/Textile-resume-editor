import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class ProfileSection(Base):
    __tablename__ = "profile_sections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    section_type: Mapped[str] = mapped_column(String(50), nullable=False)  # experience, education, project, skills, generic
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="profile_sections")
    items = relationship("ProfileItem", back_populates="section", cascade="all, delete-orphan", order_by="ProfileItem.order_index")


class ProfileItem(Base):
    __tablename__ = "profile_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    section_id: Mapped[str] = mapped_column(String(36), ForeignKey("profile_sections.id", ondelete="CASCADE"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    data: Mapped[dict] = mapped_column(JSON, default=dict)  # flexible JSON for any item type
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    section = relationship("ProfileSection", back_populates="items")
