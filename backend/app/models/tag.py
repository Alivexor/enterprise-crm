from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_tags_organization_name"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    organization: Mapped["Organization"] = relationship(back_populates="tags")
    companies: Mapped[list["Company"]] = relationship(
        secondary="company_tags", back_populates="tags"
    )
    contacts: Mapped[list["Contact"]] = relationship(
        secondary="contact_tags", back_populates="tags"
    )
    leads: Mapped[list["Lead"]] = relationship(
        secondary="lead_tags", back_populates="tags"
    )
    deals: Mapped[list["Deal"]] = relationship(
        secondary="deal_tags", back_populates="tags"
    )
