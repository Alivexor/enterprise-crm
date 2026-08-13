from uuid import UUID

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class DealTag(Base):
    __tablename__ = "deal_tags"
    __table_args__ = (Index("ix_deal_tags_tag_id", "tag_id"),)

    deal_id: Mapped[UUID] = mapped_column(
        ForeignKey("deals.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )
