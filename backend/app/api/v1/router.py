from fastapi import APIRouter

from app.api.v1.audit_logs.router import router as audit_logs_router
from app.api.v1.activities.router import router as activities_router
from app.api.v1.attachments.router import router as attachments_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.companies.router import router as companies_router
from app.api.v1.contacts.router import router as contacts_router
from app.api.v1.leads.router import router as leads_router
from app.api.v1.deals.router import router as deals_router
from app.api.v1.dashboard.router import router as dashboard_router
from app.api.v1.import_export.router import router as import_export_router
from app.api.v1.health.router import router as health_router
from app.api.v1.organization.router import router as organization_router
from app.api.v1.notes.router import router as notes_router
from app.api.v1.notifications.router import router as notifications_router
from app.api.v1.pipelines.router import router as pipelines_router
from app.api.v1.roles.router import router as roles_router
from app.api.v1.search.router import router as search_router
from app.api.v1.tasks.router import router as tasks_router
from app.api.v1.tags.router import router as tags_router
from app.api.v1.users.router import profile_router, router as users_router
from app.api.v1.v3.router import router as v3_router

router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(companies_router)
router.include_router(contacts_router)
router.include_router(leads_router)
router.include_router(pipelines_router)
router.include_router(deals_router)
router.include_router(activities_router)
router.include_router(tasks_router)
router.include_router(attachments_router)
router.include_router(notifications_router)
router.include_router(notes_router)
router.include_router(tags_router)
router.include_router(audit_logs_router)
router.include_router(organization_router)
router.include_router(roles_router)
router.include_router(users_router)
router.include_router(profile_router)
router.include_router(dashboard_router)
router.include_router(search_router)
router.include_router(import_export_router)


router.include_router(v3_router)
