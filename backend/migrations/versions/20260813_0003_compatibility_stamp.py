"""Preserve compatibility with a locally applied retired revision.

Revision ID: 20260813_0003
Revises: 20260813_0006
Create Date: 2026-08-14
"""

from alembic import op


revision = "20260813_0003"
down_revision = "20260813_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No schema change; this revision only preserves local Alembic history."""


def downgrade() -> None:
    """Restore the original contact foreign-key behavior for old local data."""
    with op.batch_alter_table(
        "contacts",
        naming_convention={"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"},
    ) as batch_op:
        batch_op.drop_constraint("fk_contacts_company_id_companies", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_contacts_company_id_companies",
            "companies",
            ["company_id"],
            ["id"],
            ondelete="CASCADE",
        )
