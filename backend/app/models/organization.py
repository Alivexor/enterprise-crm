from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    users: Mapped[list["User"]] = relationship(back_populates="organization")
    roles: Mapped[list["Role"]] = relationship(back_populates="organization")
    companies: Mapped[list["Company"]] = relationship(back_populates="organization")
    leads: Mapped[list["Lead"]] = relationship(back_populates="organization")
    pipelines: Mapped[list["Pipeline"]] = relationship(back_populates="organization")
    deals: Mapped[list["Deal"]] = relationship(back_populates="organization")
    activities: Mapped[list["Activity"]] = relationship(back_populates="organization")
    tasks: Mapped[list["Task"]] = relationship(back_populates="organization")
    notes: Mapped[list["Note"]] = relationship(back_populates="organization")
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="organization"
    )
    attachments: Mapped[list["Attachment"]] = relationship(back_populates="organization")
    refresh_sessions: Mapped[list["RefreshSession"]] = relationship(
        back_populates="organization"
    )
    tags: Mapped[list["Tag"]] = relationship(back_populates="organization")
