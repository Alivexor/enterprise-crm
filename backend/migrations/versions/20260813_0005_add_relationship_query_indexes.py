"""Add relationship query indexes.

Revision ID: 20260813_0005
Revises: 20260812_0004
Create Date: 2026-08-13
"""

from alembic import op


revision = "20260813_0005"
down_revision = "20260812_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_companies_organization_id", "companies", ["organization_id"])
    op.create_index("ix_contacts_company_id", "contacts", ["company_id"])
    op.create_index("ix_leads_contact_id", "leads", ["contact_id"])
    op.create_index("ix_activities_contact_id", "activities", ["contact_id"])
    op.create_index("ix_activities_lead_id", "activities", ["lead_id"])
    op.create_index("ix_notes_company_id", "notes", ["company_id"])
    op.create_index("ix_notes_contact_id", "notes", ["contact_id"])
    op.create_index("ix_notes_lead_id", "notes", ["lead_id"])


def downgrade() -> None:
    op.drop_index("ix_notes_lead_id", table_name="notes")
    op.drop_index("ix_notes_contact_id", table_name="notes")
    op.drop_index("ix_notes_company_id", table_name="notes")
    op.drop_index("ix_activities_lead_id", table_name="activities")
    op.drop_index("ix_activities_contact_id", table_name="activities")
    op.drop_index("ix_leads_contact_id", table_name="leads")
    op.drop_index("ix_contacts_company_id", table_name="contacts")
    op.drop_index("ix_companies_organization_id", table_name="companies")
