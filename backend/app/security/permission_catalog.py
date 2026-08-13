"""Central permission definitions used by authorization and development setup."""

from dataclasses import dataclass
from enum import StrEnum


class PermissionName(StrEnum):
    """Stable permission identifiers for Enterprise CRM capabilities."""

    ORGANIZATIONS_READ = "organizations.read"
    ORGANIZATIONS_UPDATE = "organizations.update"
    USERS_READ = "users.read"
    USERS_CREATE = "users.create"
    USERS_UPDATE = "users.update"
    USERS_DEACTIVATE = "users.deactivate"
    ROLES_READ = "roles.read"
    ROLES_CREATE = "roles.create"
    ROLES_UPDATE = "roles.update"
    ROLES_DELETE = "roles.delete"
    PERMISSIONS_READ = "permissions.read"
    COMPANIES_READ = "companies.read"
    COMPANIES_CREATE = "companies.create"
    COMPANIES_UPDATE = "companies.update"
    COMPANIES_DELETE = "companies.delete"
    CONTACTS_READ = "contacts.read"
    CONTACTS_CREATE = "contacts.create"
    CONTACTS_UPDATE = "contacts.update"
    CONTACTS_DELETE = "contacts.delete"
    LEADS_READ = "leads.read"
    LEADS_CREATE = "leads.create"
    LEADS_UPDATE = "leads.update"
    LEADS_DELETE = "leads.delete"
    PIPELINES_READ = "pipelines.read"
    PIPELINES_CREATE = "pipelines.create"
    PIPELINES_UPDATE = "pipelines.update"
    PIPELINES_DELETE = "pipelines.delete"
    DEALS_READ = "deals.read"
    DEALS_CREATE = "deals.create"
    DEALS_UPDATE = "deals.update"
    DEALS_DELETE = "deals.delete"
    ACTIVITIES_READ = "activities.read"
    ACTIVITIES_CREATE = "activities.create"
    ACTIVITIES_UPDATE = "activities.update"
    ACTIVITIES_DELETE = "activities.delete"
    TASKS_READ = "tasks.read"
    TASKS_CREATE = "tasks.create"
    TASKS_UPDATE = "tasks.update"
    TASKS_DELETE = "tasks.delete"
    NOTES_READ = "notes.read"
    NOTES_CREATE = "notes.create"
    NOTES_UPDATE = "notes.update"
    NOTES_DELETE = "notes.delete"
    TAGS_READ = "tags.read"
    TAGS_CREATE = "tags.create"
    TAGS_UPDATE = "tags.update"
    TAGS_DELETE = "tags.delete"
    AUDIT_LOGS_READ = "audit_logs.read"
    DASHBOARD_READ = "dashboard.read"
    ANALYTICS_READ = "analytics.read"
    SEARCH_READ = "search.read"
    SETTINGS_READ = "settings.read"
    SETTINGS_UPDATE = "settings.update"
    NOTIFICATIONS_READ = "notifications.read"
    NOTIFICATIONS_UPDATE = "notifications.update"
    ATTACHMENTS_READ = "attachments.read"
    ATTACHMENTS_CREATE = "attachments.create"
    ATTACHMENTS_DELETE = "attachments.delete"
    IMPORTS_CREATE = "imports.create"
    EXPORTS_CREATE = "exports.create"
    PROFILE_READ = "profile.read"
    PROFILE_UPDATE = "profile.update"
    SAVED_VIEWS_READ = "saved_views.read"
    SAVED_VIEWS_UPDATE = "saved_views.update"
    CUSTOM_FIELDS_READ = "custom_fields.read"
    CUSTOM_FIELDS_UPDATE = "custom_fields.update"
    AUTOMATIONS_READ = "automations.read"
    AUTOMATIONS_UPDATE = "automations.update"
    REPORTS_READ = "reports.read"
    DATA_QUALITY_READ = "data_quality.read"
    GOALS_READ = "goals.read"
    GOALS_UPDATE = "goals.update"
    PRODUCTS_READ = "products.read"
    PRODUCTS_UPDATE = "products.update"
    QUOTES_READ = "quotes.read"
    QUOTES_UPDATE = "quotes.update"
    QUOTES_APPROVE = "quotes.approve"
    SEQUENCES_READ = "sequences.read"
    SEQUENCES_UPDATE = "sequences.update"
    DASHBOARDS_READ = "dashboards.read"
    DASHBOARDS_UPDATE = "dashboards.update"
    MFA_MANAGE = "mfa.manage"
    AI_USE = "ai.use"
    DEVELOPER_READ = "developer.read"
    DEVELOPER_UPDATE = "developer.update"


@dataclass(frozen=True)
class PermissionDefinition:
    name: PermissionName
    description: str


def _definition(name: PermissionName) -> PermissionDefinition:
    resource, action = name.value.split(".", maxsplit=1)
    return PermissionDefinition(
        name=name,
        description=f"Allows {action.replace('_', ' ')} access to {resource.replace('_', ' ')}.",
    )


PERMISSION_CATALOG: tuple[PermissionDefinition, ...] = tuple(
    _definition(permission_name) for permission_name in PermissionName
)

DEFAULT_ADMIN_PERMISSION_NAMES: frozenset[str] = frozenset(
    definition.name.value for definition in PERMISSION_CATALOG
)
