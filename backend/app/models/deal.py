from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Deal(Base):
    __tablename__ = "deals"
    __table_args__ = (
        Index("ix_deals_organization_status", "organization_id", "status"),
        Index("ix_deals_pipeline_stage", "pipeline_id", "stage_id"),
        Index("ix_deals_assigned_user_id", "assigned_user_id"),
        Index("ix_deals_company_id", "company_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False
    )
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    contact_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    pipeline_id: Mapped[UUID] = mapped_column(
        ForeignKey("pipelines.id", ondelete="RESTRICT"), nullable=False
    )
    stage_id: Mapped[UUID] = mapped_column(
        ForeignKey("pipeline_stages.id", ondelete="RESTRICT"), nullable=False
    )
    assigned_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    probability: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    expected_close_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    organization: Mapped["Organization"] = relationship(back_populates="deals")
    company: Mapped["Company"] = relationship(back_populates="deals")
    contact: Mapped["Contact | None"] = relationship(back_populates="deals")
    pipeline: Mapped["Pipeline"] = relationship(back_populates="deals")
    stage: Mapped["PipelineStage"] = relationship(back_populates="deals")
    assigned_user: Mapped["User"] = relationship(back_populates="assigned_deals")
    tags: Mapped[list["Tag"]] = relationship(
        secondary="deal_tags", back_populates="deals"
    )
