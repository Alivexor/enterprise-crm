from __future__ import annotations

import hashlib
import hmac
import json
import math
import secrets
import ipaddress
import socket
from urllib.parse import urlparse
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Iterator
from uuid import UUID

import httpx
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.activity import Activity
from app.models.company import Company
from app.models.contact import Contact
from app.models.custom_field import CustomFieldDefinition, CustomFieldValue
from app.models.dashboard import DashboardWidget
from app.models.deal import Deal
from app.models.developer import ApiKey, WebhookDelivery, WebhookEndpoint
from app.models.lead import Lead
from app.models.notification import Notification
from app.models.note import Note
from app.models.revenue import Product, Quote, QuoteItem, SalesGoal
from app.models.saved_view import SavedView
from app.models.sequence import SalesSequence, SalesSequenceEnrollment, SalesSequenceStep
from app.models.task import Task
from app.models.user import User
from app.models.workflow import Workflow, WorkflowRun
from app.security.secret_storage import decrypt_secret, encrypt_secret
from app.schemas.v3 import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    AttentionItem,
    AiCopilotResponse,
    AiDealInsightResponse,
    AiModelResponse,
    AiStatusResponse,
    CustomFieldDefinitionCreate,
    CustomFieldDefinitionUpdate,
    CustomFieldValuesResponse,
    WebhookDeliveryResponse,
    WebhookCreatedResponse,
    QuoteApprovalRequest,
    SequenceEnrollmentResponse,
    SalesSequenceResponse,
    SalesSequenceCreate,
    DashboardWidgetResponse,
    DashboardWidgetUpdate,
    DashboardWidgetCreate,
    CurrencyForecast,
    DataQualityIssue,
    DataQualityResponse,
    LeadScoreResponse,
    MorningBriefResponse,
    ProductCreate,
    ProductUpdate,
    QuoteCreate,
    QuoteItemResponse,
    QuoteResponse,
    RelationshipHealthResponse,
    ReportBuilderResponse,
    ReportRow,
    RevenueForecastResponse,
    ForecastBucket,
    SalesGoalCreate,
    SalesGoalResponse,
    SavedViewCreate,
    SavedViewUpdate,
    WebhookCreate,
    WorkflowCreate,
    WorkflowRunResponse,
    WinLossAnalyticsResponse,
    WorkflowUpdate,
)


class V3NotFoundError(Exception):
    pass


class V3ConflictError(Exception):
    pass


class V3ValidationError(Exception):
    pass


class V3ExternalServiceError(Exception):
    pass


ENTITY_MODELS: dict[str, type] = {
    "company": Company,
    "contact": Contact,
    "lead": Lead,
    "deal": Deal,
    "task": Task,
}

ENTITY_MUTABLE_FIELDS: dict[str, frozenset[str]] = {
    "company": frozenset({"name", "website", "industry"}),
    "lead": frozenset({"title", "description", "source", "status", "assigned_user_id"}),
    "deal": frozenset({"title", "status", "probability", "expected_close_date", "assigned_user_id"}),
    "task": frozenset({"title", "description", "priority", "status", "due_date", "assigned_user_id"}),
}


class V3PlatformService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    # ----------------------------- Saved views -----------------------------
    def list_saved_views(self, db: Session, organization_id: UUID, user_id: UUID, resource: str | None) -> list[SavedView]:
        clauses = [SavedView.organization_id == organization_id, or_(SavedView.user_id == user_id, SavedView.is_shared.is_(True))]
        if resource:
            clauses.append(SavedView.resource == resource)
        return list(db.scalars(select(SavedView).where(*clauses).order_by(SavedView.resource.asc(), SavedView.name.asc())))

    def create_saved_view(self, db: Session, organization_id: UUID, user_id: UUID, data: SavedViewCreate) -> SavedView:
        view = SavedView(organization_id=organization_id, user_id=user_id, **data.model_dump())
        db.add(view)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise V3ConflictError("A saved view with this name already exists") from exc
        db.refresh(view)
        return view

    def update_saved_view(self, db: Session, organization_id: UUID, user_id: UUID, view_id: UUID, data: SavedViewUpdate) -> SavedView:
        view = db.scalar(select(SavedView).where(SavedView.id == view_id, SavedView.organization_id == organization_id, SavedView.user_id == user_id))
        if view is None:
            raise V3NotFoundError("Saved view not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(view, field, value)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise V3ConflictError("Saved view could not be updated") from exc
        db.refresh(view)
        return view

    def delete_saved_view(self, db: Session, organization_id: UUID, user_id: UUID, view_id: UUID) -> None:
        view = db.scalar(select(SavedView).where(SavedView.id == view_id, SavedView.organization_id == organization_id, SavedView.user_id == user_id))
        if view is None:
            raise V3NotFoundError("Saved view not found")
        db.delete(view)
        db.commit()

    # --------------------------- Custom fields -----------------------------
    def list_custom_fields(self, db: Session, organization_id: UUID, entity_type: str | None = None) -> list[CustomFieldDefinition]:
        clauses = [CustomFieldDefinition.organization_id == organization_id]
        if entity_type:
            clauses.append(CustomFieldDefinition.entity_type == entity_type)
        return list(db.scalars(select(CustomFieldDefinition).where(*clauses).order_by(CustomFieldDefinition.entity_type.asc(), CustomFieldDefinition.position.asc(), CustomFieldDefinition.label.asc())))

    def create_custom_field(self, db: Session, organization_id: UUID, data: CustomFieldDefinitionCreate) -> CustomFieldDefinition:
        definition = CustomFieldDefinition(organization_id=organization_id, **data.model_dump())
        db.add(definition)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise V3ConflictError("A custom field with this key already exists") from exc
        db.refresh(definition)
        return definition

    def update_custom_field(self, db: Session, organization_id: UUID, definition_id: UUID, data: CustomFieldDefinitionUpdate) -> CustomFieldDefinition:
        definition = db.scalar(select(CustomFieldDefinition).where(CustomFieldDefinition.id == definition_id, CustomFieldDefinition.organization_id == organization_id))
        if definition is None:
            raise V3NotFoundError("Custom field not found")
        changes = data.model_dump(exclude_unset=True)
        if "options" in changes and definition.data_type not in {"select", "multi_select"} and changes["options"]:
            raise V3ValidationError("Options are only supported for select fields")
        for field, value in changes.items():
            setattr(definition, field, value)
        db.commit()
        db.refresh(definition)
        return definition

    def delete_custom_field(self, db: Session, organization_id: UUID, definition_id: UUID) -> None:
        definition = db.scalar(select(CustomFieldDefinition).where(CustomFieldDefinition.id == definition_id, CustomFieldDefinition.organization_id == organization_id))
        if definition is None:
            raise V3NotFoundError("Custom field not found")
        db.delete(definition)
        db.commit()

    def get_custom_field_values(self, db: Session, organization_id: UUID, entity_type: str, entity_id: UUID) -> CustomFieldValuesResponse:
        self._require_entity(db, organization_id, entity_type, entity_id)
        definitions = self.list_custom_fields(db, organization_id, entity_type)
        ids = [definition.id for definition in definitions]
        values_by_definition: dict[UUID, Any] = {}
        if ids:
            rows = db.scalars(select(CustomFieldValue).where(CustomFieldValue.organization_id == organization_id, CustomFieldValue.entity_id == entity_id, CustomFieldValue.definition_id.in_(ids)))
            values_by_definition = {row.definition_id: row.value for row in rows}
        return CustomFieldValuesResponse(entity_type=entity_type, entity_id=entity_id, values={definition.field_key: values_by_definition.get(definition.id) for definition in definitions})

    def set_custom_field_values(self, db: Session, organization_id: UUID, actor_id: UUID, entity_type: str, entity_id: UUID, values: dict[str, Any]) -> CustomFieldValuesResponse:
        self._require_entity(db, organization_id, entity_type, entity_id)
        definitions = {definition.field_key: definition for definition in self.list_custom_fields(db, organization_id, entity_type) if definition.is_active}
        unknown = set(values) - set(definitions)
        if unknown:
            raise V3ValidationError(f"Unknown custom field(s): {', '.join(sorted(unknown))}")
        for key, raw_value in values.items():
            definition = definitions[key]
            value = self._normalize_custom_value(definition, raw_value)
            existing = db.scalar(select(CustomFieldValue).where(CustomFieldValue.definition_id == definition.id, CustomFieldValue.entity_id == entity_id))
            if existing is None:
                db.add(CustomFieldValue(organization_id=organization_id, definition_id=definition.id, entity_id=entity_id, value=value, updated_by_user_id=actor_id))
            else:
                existing.value = value
                existing.updated_by_user_id = actor_id
        db.commit()
        return self.get_custom_field_values(db, organization_id, entity_type, entity_id)

    # ------------------------------ Workflows ------------------------------
    def list_workflows(self, db: Session, organization_id: UUID) -> list[Workflow]:
        return list(db.scalars(select(Workflow).where(Workflow.organization_id == organization_id).order_by(Workflow.created_at.desc())))

    def create_workflow(self, db: Session, organization_id: UUID, data: WorkflowCreate) -> Workflow:
        workflow = Workflow(
            organization_id=organization_id,
            **data.model_dump(mode="json"),
        )
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
        return workflow

    def update_workflow(self, db: Session, organization_id: UUID, workflow_id: UUID, data: WorkflowUpdate) -> Workflow:
        workflow = self._get_workflow(db, organization_id, workflow_id)
        for field, value in data.model_dump(exclude_unset=True, mode="json").items():
            setattr(workflow, field, value)
        db.commit()
        db.refresh(workflow)
        return workflow

    def delete_workflow(self, db: Session, organization_id: UUID, workflow_id: UUID) -> None:
        workflow = self._get_workflow(db, organization_id, workflow_id)
        db.delete(workflow)
        db.commit()

    def run_workflow(self, db: Session, organization_id: UUID, actor_id: UUID, workflow_id: UUID, entity_id: UUID | None, payload: dict[str, Any]) -> WorkflowRun:
        workflow = self._get_workflow(db, organization_id, workflow_id)
        if not workflow.is_active:
            raise V3ValidationError("Workflow is disabled")
        merged_payload = dict(payload)
        if entity_id is not None:
            entity_payload = self._entity_snapshot(db, organization_id, workflow.entity_type, entity_id)
            merged_payload = {**entity_payload, **merged_payload}
        return self._execute_workflow(db, workflow, actor_id, entity_id, merged_payload, commit=True)

    def emit_event(self, db: Session, *, organization_id: UUID, actor_id: UUID, event_type: str, entity_type: str, entity_id: UUID, payload: dict[str, Any]) -> list[WorkflowRun]:
        workflows = list(db.scalars(select(Workflow).where(Workflow.organization_id == organization_id, Workflow.event_type == event_type, Workflow.entity_type == entity_type, Workflow.is_active.is_(True))))
        runs: list[WorkflowRun] = []
        for workflow in workflows:
            if self._conditions_match(workflow.conditions, payload):
                runs.append(self._execute_workflow(db, workflow, actor_id, entity_id, payload, commit=False))
        self.enqueue_webhook_event(db, organization_id, event_type, {"entity_type": entity_type, "entity_id": str(entity_id), **payload})
        return runs

    def _execute_workflow(self, db: Session, workflow: Workflow, actor_id: UUID, entity_id: UUID | None, payload: dict[str, Any], *, commit: bool) -> WorkflowRun:
        run = WorkflowRun(organization_id=workflow.organization_id, workflow_id=workflow.id, actor_id=actor_id, status="running", event_type=workflow.event_type, entity_id=entity_id, input_payload=payload, output_payload={})
        db.add(run)
        outputs: list[dict[str, Any]] = []
        try:
            for action in workflow.actions:
                outputs.append(self._execute_action(db, workflow, actor_id, entity_id, payload, action))
            run.status = "succeeded"
            run.output_payload = {"actions": outputs}
            workflow.run_count += 1
            workflow.last_run_at = datetime.now(timezone.utc)
            db.flush()
            if commit:
                db.commit()
                db.refresh(run)
        except Exception as exc:
            run.status = "failed"
            run.error = str(exc)[:4000]
            db.flush()
            if commit:
                db.commit()
                db.refresh(run)
        return run

    def _execute_action(self, db: Session, workflow: Workflow, actor_id: UUID, entity_id: UUID | None, payload: dict[str, Any], action: dict[str, Any]) -> dict[str, Any]:
        action_type = action.get("type")
        config = action.get("config") or {}
        if action_type == "create_task":
            target_user = self._resolve_workflow_user(config.get("assigned_user_id"), actor_id, payload)
            due_days = int(config.get("due_days", 1))
            task = Task(
                organization_id=workflow.organization_id,
                assigned_user_id=target_user,
                title=str(config.get("title") or f"Workflow: {workflow.name}")[:255],
                description=str(config.get("description") or "Created by workflow automation")[:20_000],
                priority=str(config.get("priority") or "medium"),
                status="open",
                due_date=datetime.now(timezone.utc) + timedelta(days=max(-365, min(due_days, 3650))),
            )
            db.add(task)
            db.flush()
            return {"type": action_type, "task_id": str(task.id)}
        if action_type == "notify_user":
            target_user = self._resolve_workflow_user(config.get("user_id"), actor_id, payload)
            notification = Notification(
                organization_id=workflow.organization_id,
                user_id=target_user,
                type="workflow",
                title=str(config.get("title") or workflow.name)[:255],
                body=str(config.get("body") or "Workflow automation requires your attention")[:20_000],
                entity_type=workflow.entity_type,
                entity_id=entity_id,
            )
            db.add(notification)
            db.flush()
            return {"type": action_type, "notification_id": str(notification.id)}
        if action_type == "set_field":
            if entity_id is None:
                raise V3ValidationError("set_field requires an entity")
            field = str(config.get("field") or "")
            if field not in ENTITY_MUTABLE_FIELDS.get(workflow.entity_type, frozenset()):
                raise V3ValidationError(f"Field {field!r} is not allowed for workflow updates")
            entity = self._require_entity(db, workflow.organization_id, workflow.entity_type, entity_id)
            value = config.get("value")
            if field in {"assigned_user_id"} and isinstance(value, str):
                value = UUID(value)
            if field == "probability":
                value = Decimal(str(value))
                if value < 0 or value > 100:
                    raise V3ValidationError("Probability must be between 0 and 100")
            if field == "expected_close_date" and isinstance(value, str):
                value = date.fromisoformat(value)
            if field == "due_date" and isinstance(value, str):
                value = datetime.fromisoformat(value.replace("Z", "+00:00"))
            setattr(entity, field, value)
            db.flush()
            return {"type": action_type, "field": field}
        raise V3ValidationError(f"Unsupported workflow action: {action_type}")

    # ------------------------- Data quality / intel ------------------------
    def data_quality(self, db: Session, organization_id: UUID) -> DataQualityResponse:
        issues: list[DataQualityIssue] = []
        now = datetime.now(timezone.utc)

        duplicate_groups = list(db.execute(
            select(func.lower(Company.name), func.count(Company.id))
            .where(Company.organization_id == organization_id)
            .group_by(func.lower(Company.name)).having(func.count(Company.id) > 1)
        ))
        duplicate_count = sum(max(0, int(count) - 1) for _, count in duplicate_groups)
        if duplicate_count:
            issues.append(DataQualityIssue(code="duplicate_companies", severity="high", title="Possible duplicate companies", count=duplicate_count, resource="companies"))

        missing_contact_count = int(db.scalar(
            select(func.count(Contact.id)).join(Company, Contact.company_id == Company.id).where(
                Company.organization_id == organization_id,
                Contact.email.is_(None), Contact.phone.is_(None),
            )
        ) or 0)
        if missing_contact_count:
            issues.append(DataQualityIssue(code="contacts_without_reachability", severity="medium", title="Contacts missing both email and phone", count=missing_contact_count, resource="contacts"))

        stale_lead_before = now - timedelta(days=30)
        stale_leads = list(db.scalars(select(Lead.id).where(Lead.organization_id == organization_id, Lead.status.not_in(("converted", "lost")), Lead.updated_at < stale_lead_before).limit(20)))
        stale_lead_count = int(db.scalar(select(func.count(Lead.id)).where(Lead.organization_id == organization_id, Lead.status.not_in(("converted", "lost")), Lead.updated_at < stale_lead_before)) or 0)
        if stale_lead_count:
            issues.append(DataQualityIssue(code="stale_leads", severity="medium", title="Open leads untouched for 30+ days", count=stale_lead_count, resource="leads", sample_ids=stale_leads))

        overdue_deals = list(db.scalars(select(Deal.id).where(Deal.organization_id == organization_id, Deal.status == "open", Deal.expected_close_date < now.date()).limit(20)))
        overdue_deal_count = int(db.scalar(select(func.count(Deal.id)).where(Deal.organization_id == organization_id, Deal.status == "open", Deal.expected_close_date < now.date())) or 0)
        if overdue_deal_count:
            issues.append(DataQualityIssue(code="past_close_date_deals", severity="high", title="Open deals past expected close date", count=overdue_deal_count, resource="deals", sample_ids=overdue_deals))

        overdue_tasks = list(db.scalars(select(Task.id).where(Task.organization_id == organization_id, Task.status.not_in(("completed", "cancelled")), Task.due_date.is_not(None), Task.due_date < now).limit(20)))
        overdue_task_count = int(db.scalar(select(func.count(Task.id)).where(Task.organization_id == organization_id, Task.status.not_in(("completed", "cancelled")), Task.due_date.is_not(None), Task.due_date < now)) or 0)
        if overdue_task_count:
            issues.append(DataQualityIssue(code="overdue_tasks", severity="medium", title="Overdue open tasks", count=overdue_task_count, resource="tasks", sample_ids=overdue_tasks))

        no_contact_companies = int(db.scalar(
            select(func.count(Company.id)).where(Company.organization_id == organization_id, ~select(Contact.id).where(Contact.company_id == Company.id).exists())
        ) or 0)
        if no_contact_companies:
            issues.append(DataQualityIssue(code="companies_without_contacts", severity="low", title="Companies without contacts", count=no_contact_companies, resource="companies"))

        weights = {"low": 1, "medium": 2, "high": 4}
        weighted = sum(issue.count * weights[issue.severity] for issue in issues)
        total_issues = sum(issue.count for issue in issues)
        score = max(0, 100 - min(100, int(math.sqrt(weighted) * 7)))
        return DataQualityResponse(score=score, total_issues=total_issues, issues=issues)

    def morning_brief(self, db: Session, organization_id: UUID, user_id: UUID) -> MorningBriefResponse:
        now = datetime.now(timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        stale_before = now - timedelta(days=14)
        closing_before = now.date() + timedelta(days=14)
        open_task_clause = Task.status.not_in(("completed", "cancelled"))

        overdue_tasks = int(db.scalar(select(func.count(Task.id)).where(
            Task.organization_id == organization_id, Task.assigned_user_id == user_id, open_task_clause,
            Task.due_date.is_not(None), Task.due_date < now,
        )) or 0)
        due_today = int(db.scalar(select(func.count(Task.id)).where(
            Task.organization_id == organization_id, Task.assigned_user_id == user_id, open_task_clause,
            Task.due_date >= day_start, Task.due_date < day_end,
        )) or 0)
        stale_leads = int(db.scalar(select(func.count(Lead.id)).where(
            Lead.organization_id == organization_id, Lead.assigned_user_id == user_id,
            Lead.status.not_in(("converted", "lost")), Lead.updated_at < stale_before,
        )) or 0)
        closing_soon = int(db.scalar(select(func.count(Deal.id)).where(
            Deal.organization_id == organization_id, Deal.assigned_user_id == user_id, Deal.status == "open",
            Deal.expected_close_date <= closing_before,
        )) or 0)

        actions: list[AttentionItem] = []
        overdue_rows = list(db.scalars(select(Task).where(
            Task.organization_id == organization_id, Task.assigned_user_id == user_id, open_task_clause,
            Task.due_date.is_not(None), Task.due_date < now,
        ).order_by(Task.due_date.asc()).limit(6)))
        for task in overdue_rows:
            actions.append(AttentionItem(kind="task", entity_id=task.id, title=task.title, reason="Task is overdue", priority="high", route=f"/dashboard/tasks/{task.id}"))

        deal_rows = list(db.scalars(select(Deal).where(
            Deal.organization_id == organization_id, Deal.assigned_user_id == user_id, Deal.status == "open",
            Deal.expected_close_date <= closing_before,
        ).order_by(Deal.expected_close_date.asc(), Deal.probability.desc()).limit(6)))
        for deal in deal_rows:
            priority = "high" if deal.expected_close_date < now.date() or deal.probability >= 75 else "medium"
            reason = "Expected close date has passed" if deal.expected_close_date < now.date() else "Deal is closing within 14 days"
            actions.append(AttentionItem(kind="deal", entity_id=deal.id, title=deal.title, reason=reason, priority=priority, route=f"/dashboard/deals/{deal.id}"))

        lead_rows = list(db.scalars(select(Lead).where(
            Lead.organization_id == organization_id, Lead.assigned_user_id == user_id,
            Lead.status.not_in(("converted", "lost")), Lead.updated_at < stale_before,
        ).order_by(Lead.updated_at.asc()).limit(5)))
        for lead in lead_rows:
            actions.append(AttentionItem(kind="lead", entity_id=lead.id, title=lead.title, reason="Lead has been untouched for 14+ days", priority="medium", route=f"/dashboard/leads/{lead.id}"))

        activity_rows = list(db.scalars(select(Activity).where(
            Activity.organization_id == organization_id, Activity.user_id == user_id, Activity.completed.is_(False),
            Activity.due_date.is_not(None), Activity.due_date <= now + timedelta(days=2),
        ).order_by(Activity.due_date.asc()).limit(5)))
        for activity in activity_rows:
            actions.append(AttentionItem(kind="activity", entity_id=activity.id, title=activity.title, reason="Activity is due soon", priority="medium", route=f"/dashboard/activities/{activity.id}"))

        rank = {"high": 0, "medium": 1, "low": 2}
        actions.sort(key=lambda item: (rank[item.priority], item.kind, item.title.lower()))
        return MorningBriefResponse(
            generated_at=now, overdue_tasks=overdue_tasks, due_today=due_today, stale_leads=stale_leads,
            closing_soon_deals=closing_soon, actions=actions[:16],
        )

    def lead_score(self, db: Session, organization_id: UUID, lead_id: UUID) -> LeadScoreResponse:
        lead = db.scalar(select(Lead).where(Lead.id == lead_id, Lead.organization_id == organization_id))
        if lead is None:
            raise V3NotFoundError("Lead not found")
        score = 20
        factors: list[str] = []
        next_actions: list[str] = []
        status_points = {"qualified": 30, "new": 12, "unqualified": -20, "lost": -40, "converted": 35}
        score += status_points.get(lead.status, 0)
        factors.append(f"Lifecycle status: {lead.status}")

        if lead.company_id is not None:
            score += 10; factors.append("Company is identified")
        else:
            next_actions.append("Associate this lead with a company")
        contact = db.scalar(select(Contact).where(Contact.id == lead.contact_id)) if lead.contact_id else None
        if contact is not None:
            score += 10; factors.append("Contact is identified")
            if contact.email:
                score += 8; factors.append("Email is available")
            else:
                next_actions.append("Add a verified email address")
            if contact.phone:
                score += 7; factors.append("Phone is available")
            else:
                next_actions.append("Add a phone number")
        else:
            next_actions.append("Associate a contact with this lead")

        normalized_source = (lead.source or "").strip().lower()
        if normalized_source in {"referral", "partner"}:
            score += 12; factors.append("High-intent referral source")
        elif normalized_source in {"website", "inbound", "demo", "event"}:
            score += 8; factors.append("Inbound source")
        elif normalized_source:
            score += 3

        activity_count = int(db.scalar(select(func.count(Activity.id)).where(
            Activity.organization_id == organization_id, Activity.lead_id == lead.id,
            Activity.created_at >= datetime.now(timezone.utc) - timedelta(days=14),
        )) or 0)
        if activity_count:
            score += min(15, activity_count * 5); factors.append(f"{activity_count} recent interaction(s)")
        else:
            next_actions.append("Schedule the next follow-up")

        updated_at = lead.updated_at if lead.updated_at.tzinfo else lead.updated_at.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - updated_at).days
        if age_days <= 7:
            score += 8; factors.append("Recently updated")
        elif age_days > 30:
            score -= 15; factors.append("Lead is stale")
            next_actions.append("Re-qualify or close this stale lead")

        score = max(0, min(100, score))
        grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 45 else "D"
        if lead.status == "new":
            next_actions.insert(0, "Qualify the lead against your sales criteria")
        return LeadScoreResponse(lead_id=lead.id, score=score, grade=grade, factors=factors[:10], next_actions=next_actions[:6])

    def win_loss_analytics(self, db: Session, organization_id: UUID) -> WinLossAnalyticsResponse:
        won = list(db.scalars(select(Deal).where(Deal.organization_id == organization_id, Deal.status == "won")))
        lost = list(db.scalars(select(Deal).where(Deal.organization_id == organization_id, Deal.status == "lost")))
        open_count = int(db.scalar(select(func.count(Deal.id)).where(Deal.organization_id == organization_id, Deal.status == "open")) or 0)
        decided = len(won) + len(lost)
        win_rate = (Decimal(len(won)) * Decimal("100") / Decimal(decided)).quantize(Decimal("0.01")) if decided else Decimal("0")
        won_by_currency: dict[str, Decimal] = {}
        lost_by_currency: dict[str, Decimal] = {}
        won_counts: dict[str, int] = {}
        for deal in won:
            won_by_currency[deal.currency] = won_by_currency.get(deal.currency, Decimal("0")) + deal.value
            won_counts[deal.currency] = won_counts.get(deal.currency, 0) + 1
        for deal in lost:
            lost_by_currency[deal.currency] = lost_by_currency.get(deal.currency, Decimal("0")) + deal.value
        average = {currency: (value / Decimal(won_counts[currency])).quantize(Decimal("0.01")) for currency, value in won_by_currency.items()}
        return WinLossAnalyticsResponse(
            won_count=len(won), lost_count=len(lost), open_count=open_count, win_rate=win_rate,
            won_value_by_currency=won_by_currency, lost_value_by_currency=lost_by_currency, average_won_value_by_currency=average,
        )

    def revenue_forecast(self, db: Session, organization_id: UUID) -> RevenueForecastResponse:
        open_deals = list(db.scalars(select(Deal).where(Deal.organization_id == organization_id, Deal.status == "open")))
        won_deals = list(db.scalars(select(Deal).where(Deal.organization_id == organization_id, Deal.status == "won")))
        currencies = sorted({deal.currency for deal in open_deals + won_deals})
        breakdown: list[CurrencyForecast] = []
        for code in currencies:
            code_open = [deal for deal in open_deals if deal.currency == code]
            code_won = [deal for deal in won_deals if deal.currency == code]
            breakdown.append(CurrencyForecast(
                currency=code,
                open_pipeline=sum((deal.value for deal in code_open), Decimal("0")),
                weighted_pipeline=sum((deal.value * deal.probability / Decimal("100") for deal in code_open), Decimal("0")),
                won_revenue=sum((deal.value for deal in code_won), Decimal("0")),
                commit=sum((deal.value for deal in code_open if deal.probability >= 80), Decimal("0")),
                best_case=sum((deal.value for deal in code_open if deal.probability >= 50), Decimal("0")),
            ))

        currency = currencies[0] if len(currencies) == 1 else None
        if currency is None:
            return RevenueForecastResponse(
                currency=None,
                open_pipeline=Decimal("0"), weighted_pipeline=Decimal("0"), won_revenue=Decimal("0"),
                commit=Decimal("0"), best_case=Decimal("0"), pipeline=Decimal("0"), buckets=[],
                currency_breakdown=breakdown,
            )

        open_pipeline = sum((deal.value for deal in open_deals), Decimal("0"))
        weighted = sum((deal.value * deal.probability / Decimal("100") for deal in open_deals), Decimal("0"))
        won = sum((deal.value for deal in won_deals), Decimal("0"))
        commit = sum((deal.value for deal in open_deals if deal.probability >= 80), Decimal("0"))
        best_case = sum((deal.value for deal in open_deals if deal.probability >= 50), Decimal("0"))
        buckets = []
        for label, minimum, maximum in (("Low confidence", 0, 49.999), ("Best case", 50, 79.999), ("Commit", 80, 100)):
            matching = [deal for deal in open_deals if Decimal(str(minimum)) <= deal.probability <= Decimal(str(maximum))]
            buckets.append(ForecastBucket(label=label, deal_count=len(matching), total_value=sum((deal.value for deal in matching), Decimal("0")), weighted_value=sum((deal.value * deal.probability / Decimal("100") for deal in matching), Decimal("0"))))
        return RevenueForecastResponse(currency=currency, open_pipeline=open_pipeline, weighted_pipeline=weighted, won_revenue=won, commit=commit, best_case=best_case, pipeline=open_pipeline, buckets=buckets, currency_breakdown=breakdown)

    def report_builder(self, db: Session, organization_id: UUID, resource: str, metric: str, group_by: str) -> ReportBuilderResponse:
        models = {
            "deals": Deal,
            "leads": Lead,
            "tasks": Task,
            "activities": Activity,
        }
        model = models.get(resource)
        if model is None:
            raise V3ValidationError("Unsupported report resource")

        allowed_groups: dict[str, dict[str, Any]] = {
            "deals": {"status": Deal.status, "pipeline": Deal.pipeline_id, "stage": Deal.stage_id, "owner": Deal.assigned_user_id, "currency": Deal.currency},
            "leads": {"status": Lead.status, "source": Lead.source, "owner": Lead.assigned_user_id},
            "tasks": {"status": Task.status, "priority": Task.priority, "owner": Task.assigned_user_id},
            "activities": {"type": Activity.type, "completed": Activity.completed, "owner": Activity.user_id},
        }
        group_column = allowed_groups[resource].get(group_by)
        if group_column is None:
            raise V3ValidationError("Unsupported group_by field for this resource")

        if metric == "count":
            value_expression = func.count(model.id)
        elif resource == "deals" and metric == "sum_value":
            value_expression = func.coalesce(func.sum(Deal.value), 0)
        elif resource == "deals" and metric == "weighted_value":
            value_expression = func.coalesce(func.sum(Deal.value * Deal.probability / Decimal("100")), 0)
        else:
            raise V3ValidationError("Unsupported metric for this resource")

        statement = (
            select(group_column, value_expression, func.count(model.id))
            .where(model.organization_id == organization_id)
            .group_by(group_column)
            .order_by(value_expression.desc())
            .limit(100)
        )
        rows: list[ReportRow] = []
        total = Decimal("0")
        for label, value, count in db.execute(statement):
            numeric = Decimal(str(value or 0))
            total += numeric
            rows.append(ReportRow(label=str(label if label is not None else "Unassigned"), value=numeric, count=int(count or 0)))
        return ReportBuilderResponse(resource=resource, metric=metric, group_by=group_by, rows=rows, total=total)

    def relationship_health(self, db: Session, organization_id: UUID, company_id: UUID) -> RelationshipHealthResponse:
        company = db.scalar(select(Company).where(Company.id == company_id, Company.organization_id == organization_id))
        if company is None:
            raise V3NotFoundError("Company not found")
        now = datetime.now(timezone.utc)
        last_activity = db.scalar(select(func.max(Activity.created_at)).where(Activity.organization_id == organization_id, Activity.company_id == company_id))
        activities_30d = int(db.scalar(select(func.count(Activity.id)).where(Activity.organization_id == organization_id, Activity.company_id == company_id, Activity.created_at >= now - timedelta(days=30))) or 0)
        open_deals = list(db.scalars(select(Deal).where(Deal.organization_id == organization_id, Deal.company_id == company_id, Deal.status == "open")))
        overdue_tasks = 0  # Tasks are not directly related to a company in the current data model.
        factors: list[str] = []
        score = 50
        if last_activity is None:
            score -= 25; factors.append("No recorded activity")
        else:
            age = now - (last_activity if last_activity.tzinfo else last_activity.replace(tzinfo=timezone.utc))
            if age.days <= 7: score += 20; factors.append("Recent engagement")
            elif age.days <= 30: score += 5; factors.append("Engagement within 30 days")
            else: score -= 15; factors.append("Relationship is cooling")
        score += min(15, activities_30d * 3)
        if open_deals: score += 10; factors.append("Active commercial opportunity")
        if overdue_tasks: score -= min(20, overdue_tasks * 4); factors.append("Overdue follow-ups exist")
        score = max(0, min(100, score))
        label = "healthy" if score >= 75 else "watch" if score >= 50 else "at_risk"
        return RelationshipHealthResponse(company_id=company_id, score=score, label=label, last_activity_at=last_activity, activities_30d=activities_30d, open_deals=len(open_deals), open_deal_value=sum((deal.value for deal in open_deals), Decimal("0")), overdue_tasks=overdue_tasks, factors=factors)

    # ---------------------------- Revenue goals ----------------------------
    def list_goals(self, db: Session, organization_id: UUID) -> list[SalesGoalResponse]:
        goals = list(db.scalars(select(SalesGoal).where(SalesGoal.organization_id == organization_id).order_by(SalesGoal.start_date.desc())))
        return [self._goal_response(db, goal) for goal in goals]

    def create_goal(self, db: Session, organization_id: UUID, data: SalesGoalCreate) -> SalesGoalResponse:
        if data.user_id is not None:
            user = db.scalar(select(User).where(User.id == data.user_id, User.organization_id == organization_id, User.is_active.is_(True)))
            if user is None:
                raise V3ValidationError("Goal user is not available")
        goal = SalesGoal(organization_id=organization_id, **data.model_dump())
        db.add(goal); db.commit(); db.refresh(goal)
        return self._goal_response(db, goal)

    def delete_goal(self, db: Session, organization_id: UUID, goal_id: UUID) -> None:
        goal = db.scalar(select(SalesGoal).where(SalesGoal.id == goal_id, SalesGoal.organization_id == organization_id))
        if goal is None: raise V3NotFoundError("Goal not found")
        db.delete(goal); db.commit()

    def _goal_response(self, db: Session, goal: SalesGoal) -> SalesGoalResponse:
        start_dt = datetime.combine(goal.start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(goal.end_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
        user_clause = []
        if goal.user_id is not None:
            if goal.metric in {"won_revenue", "won_deals"}: user_clause = [Deal.assigned_user_id == goal.user_id]
            elif goal.metric in {"created_leads", "converted_leads"}: user_clause = [Lead.assigned_user_id == goal.user_id]
            elif goal.metric == "activities_completed": user_clause = [Activity.user_id == goal.user_id]
        if goal.metric == "won_revenue":
            current = Decimal(db.scalar(select(func.coalesce(func.sum(Deal.value), 0)).where(Deal.organization_id == goal.organization_id, Deal.status == "won", Deal.updated_at >= start_dt, Deal.updated_at < end_dt, *user_clause)) or 0)
        elif goal.metric == "won_deals":
            current = Decimal(int(db.scalar(select(func.count(Deal.id)).where(Deal.organization_id == goal.organization_id, Deal.status == "won", Deal.updated_at >= start_dt, Deal.updated_at < end_dt, *user_clause)) or 0))
        elif goal.metric == "created_leads":
            current = Decimal(int(db.scalar(select(func.count(Lead.id)).where(Lead.organization_id == goal.organization_id, Lead.created_at >= start_dt, Lead.created_at < end_dt, *user_clause)) or 0))
        elif goal.metric == "converted_leads":
            current = Decimal(int(db.scalar(select(func.count(Lead.id)).where(Lead.organization_id == goal.organization_id, Lead.status == "converted", Lead.updated_at >= start_dt, Lead.updated_at < end_dt, *user_clause)) or 0))
        else:
            current = Decimal(int(db.scalar(select(func.count(Activity.id)).where(Activity.organization_id == goal.organization_id, Activity.completed.is_(True), Activity.created_at >= start_dt, Activity.created_at < end_dt, *user_clause)) or 0))
        progress = min(Decimal("999.99"), (current * 100 / goal.target_value) if goal.target_value else Decimal("0"))
        return SalesGoalResponse(id=goal.id, user_id=goal.user_id, name=goal.name, metric=goal.metric, target_value=goal.target_value, currency=goal.currency, start_date=goal.start_date, end_date=goal.end_date, current_value=current, progress_percent=progress.quantize(Decimal("0.01")), created_at=goal.created_at)

    # ------------------------- Products and quotes -------------------------
    def list_products(self, db: Session, organization_id: UUID, include_inactive: bool = False) -> list[Product]:
        clauses = [Product.organization_id == organization_id]
        if not include_inactive: clauses.append(Product.is_active.is_(True))
        return list(db.scalars(select(Product).where(*clauses).order_by(Product.name.asc())))

    def create_product(self, db: Session, organization_id: UUID, data: ProductCreate) -> Product:
        product = Product(organization_id=organization_id, **data.model_dump())
        db.add(product)
        try: db.commit()
        except IntegrityError as exc:
            db.rollback(); raise V3ConflictError("SKU already exists") from exc
        db.refresh(product); return product

    def update_product(self, db: Session, organization_id: UUID, product_id: UUID, data: ProductUpdate) -> Product:
        product = db.scalar(select(Product).where(Product.id == product_id, Product.organization_id == organization_id))
        if product is None: raise V3NotFoundError("Product not found")
        for field, value in data.model_dump(exclude_unset=True).items(): setattr(product, field, value)
        db.commit(); db.refresh(product); return product

    def create_quote(self, db: Session, organization_id: UUID, actor_id: UUID, data: QuoteCreate) -> QuoteResponse:
        company = db.scalar(select(Company).where(Company.id == data.company_id, Company.organization_id == organization_id))
        if company is None: raise V3ValidationError("Company not found")
        if data.contact_id:
            contact = db.scalar(select(Contact).where(Contact.id == data.contact_id, Contact.company_id == company.id))
            if contact is None: raise V3ValidationError("Contact does not belong to company")
        if data.deal_id:
            deal = db.scalar(select(Deal).where(Deal.id == data.deal_id, Deal.organization_id == organization_id, Deal.company_id == company.id))
            if deal is None: raise V3ValidationError("Deal does not belong to company")
        quote_payload = data.model_dump(exclude={"items"})
        if data.discount_percent >= Decimal(str(self.settings.quote_approval_discount_threshold)) and data.status == "draft":
            quote_payload["status"] = "pending_approval"
        quote = Quote(organization_id=organization_id, owner_user_id=actor_id, **quote_payload)
        db.add(quote); db.flush()
        for index, item in enumerate(data.items):
            if item.product_id:
                product = db.scalar(select(Product).where(Product.id == item.product_id, Product.organization_id == organization_id))
                if product is None: raise V3ValidationError("Quote product not found")
            db.add(QuoteItem(organization_id=organization_id, quote_id=quote.id, position=index, **item.model_dump()))
        try: db.commit()
        except IntegrityError as exc:
            db.rollback(); raise V3ConflictError("Quote number already exists") from exc
        return self.get_quote(db, organization_id, quote.id)

    def list_quotes(self, db: Session, organization_id: UUID) -> list[QuoteResponse]:
        quotes = list(db.scalars(select(Quote).where(Quote.organization_id == organization_id).order_by(Quote.created_at.desc())))
        return [self._quote_response(db, quote) for quote in quotes]

    def get_quote(self, db: Session, organization_id: UUID, quote_id: UUID) -> QuoteResponse:
        quote = db.scalar(select(Quote).where(Quote.id == quote_id, Quote.organization_id == organization_id))
        if quote is None: raise V3NotFoundError("Quote not found")
        return self._quote_response(db, quote)

    def _quote_response(self, db: Session, quote: Quote) -> QuoteResponse:
        rows = list(db.scalars(select(QuoteItem).where(QuoteItem.quote_id == quote.id, QuoteItem.organization_id == quote.organization_id).order_by(QuoteItem.position.asc())))
        item_responses = [QuoteItemResponse(id=item.id, product_id=item.product_id, description=item.description, quantity=item.quantity, unit_price=item.unit_price, line_total=(item.quantity * item.unit_price).quantize(Decimal("0.01"))) for item in rows]
        subtotal = sum((item.line_total for item in item_responses), Decimal("0"))
        discount_total = (subtotal * quote.discount_percent / Decimal("100")).quantize(Decimal("0.01"))
        taxable = subtotal - discount_total
        tax_total = (taxable * quote.tax_percent / Decimal("100")).quantize(Decimal("0.01"))
        grand_total = taxable + tax_total
        return QuoteResponse(id=quote.id, deal_id=quote.deal_id, company_id=quote.company_id, contact_id=quote.contact_id, owner_user_id=quote.owner_user_id, quote_number=quote.quote_number, status=quote.status, currency=quote.currency, discount_percent=quote.discount_percent, tax_percent=quote.tax_percent, valid_until=quote.valid_until, notes=quote.notes, approved_by_user_id=quote.approved_by_user_id, approved_at=quote.approved_at, approval_note=quote.approval_note, subtotal=subtotal, discount_total=discount_total, tax_total=tax_total, grand_total=grand_total, items=item_responses, created_at=quote.created_at, updated_at=quote.updated_at)

    def approve_quote(self, db: Session, organization_id: UUID, actor_id: UUID, quote_id: UUID, data: QuoteApprovalRequest, *, approved: bool) -> QuoteResponse:
        quote = db.scalar(select(Quote).where(Quote.id == quote_id, Quote.organization_id == organization_id))
        if quote is None:
            raise V3NotFoundError("Quote not found")
        if quote.status not in {"pending_approval", "draft"}:
            raise V3ConflictError("Quote is not awaiting approval")
        quote.status = "approved" if approved else "rejected"
        quote.approved_by_user_id = actor_id if approved else None
        quote.approved_at = datetime.now(timezone.utc) if approved else None
        quote.approval_note = data.note
        db.commit()
        return self._quote_response(db, quote)

    # ---------------------- Personal dashboard widgets --------------------
    def list_dashboard_widgets(self, db: Session, organization_id: UUID, user_id: UUID) -> list[DashboardWidget]:
        return list(db.scalars(select(DashboardWidget).where(DashboardWidget.organization_id == organization_id, DashboardWidget.user_id == user_id).order_by(DashboardWidget.position.asc(), DashboardWidget.created_at.asc())))

    def create_dashboard_widget(self, db: Session, organization_id: UUID, user_id: UUID, data: DashboardWidgetCreate) -> DashboardWidget:
        if data.widget_type == "report":
            resource = str(data.config.get("resource") or "")
            metric = str(data.config.get("metric") or "")
            group_by = str(data.config.get("group_by") or "")
            self.report_builder(db, organization_id, resource, metric, group_by)
        widget = DashboardWidget(organization_id=organization_id, user_id=user_id, **data.model_dump())
        db.add(widget); db.commit(); db.refresh(widget); return widget

    def update_dashboard_widget(self, db: Session, organization_id: UUID, user_id: UUID, widget_id: UUID, data: DashboardWidgetUpdate) -> DashboardWidget:
        widget = db.scalar(select(DashboardWidget).where(DashboardWidget.id == widget_id, DashboardWidget.organization_id == organization_id, DashboardWidget.user_id == user_id))
        if widget is None: raise V3NotFoundError("Dashboard widget not found")
        for field, value in data.model_dump(exclude_unset=True).items(): setattr(widget, field, value)
        db.commit(); db.refresh(widget); return widget

    def delete_dashboard_widget(self, db: Session, organization_id: UUID, user_id: UUID, widget_id: UUID) -> None:
        widget = db.scalar(select(DashboardWidget).where(DashboardWidget.id == widget_id, DashboardWidget.organization_id == organization_id, DashboardWidget.user_id == user_id))
        if widget is None: raise V3NotFoundError("Dashboard widget not found")
        db.delete(widget); db.commit()

    # -------------------------- Sales sequences ---------------------------
    def list_sequences(self, db: Session, organization_id: UUID) -> list[SalesSequenceResponse]:
        sequences = list(db.scalars(select(SalesSequence).where(SalesSequence.organization_id == organization_id).order_by(SalesSequence.created_at.desc())))
        result: list[SalesSequenceResponse] = []
        for sequence in sequences:
            steps = list(db.scalars(select(SalesSequenceStep).where(SalesSequenceStep.sequence_id == sequence.id).order_by(SalesSequenceStep.position.asc())))
            enrollment_count = int(db.scalar(select(func.count(SalesSequenceEnrollment.id)).where(SalesSequenceEnrollment.sequence_id == sequence.id)) or 0)
            result.append(SalesSequenceResponse(id=sequence.id, name=sequence.name, description=sequence.description, entity_type=sequence.entity_type, is_active=sequence.is_active, steps=steps, enrollment_count=enrollment_count, created_at=sequence.created_at, updated_at=sequence.updated_at))
        return result

    def create_sequence(self, db: Session, organization_id: UUID, data: SalesSequenceCreate) -> SalesSequenceResponse:
        sequence = SalesSequence(organization_id=organization_id, name=data.name, description=data.description, entity_type=data.entity_type, is_active=data.is_active)
        db.add(sequence); db.flush()
        for index, step in enumerate(data.steps):
            db.add(SalesSequenceStep(organization_id=organization_id, sequence_id=sequence.id, position=index, delay_days=step.delay_days, action_type=step.action_type, config=step.config))
        db.commit()
        return next(item for item in self.list_sequences(db, organization_id) if item.id == sequence.id)

    def delete_sequence(self, db: Session, organization_id: UUID, sequence_id: UUID) -> None:
        sequence = db.scalar(select(SalesSequence).where(SalesSequence.id == sequence_id, SalesSequence.organization_id == organization_id))
        if sequence is None: raise V3NotFoundError("Sequence not found")
        db.delete(sequence); db.commit()

    def enroll_sequence(self, db: Session, organization_id: UUID, actor_id: UUID, sequence_id: UUID, entity_id: UUID, owner_user_id: UUID | None = None) -> SalesSequenceEnrollment:
        sequence = db.scalar(select(SalesSequence).where(SalesSequence.id == sequence_id, SalesSequence.organization_id == organization_id, SalesSequence.is_active.is_(True)))
        if sequence is None: raise V3NotFoundError("Active sequence not found")
        entity = self._require_entity(db, organization_id, sequence.entity_type, entity_id)
        existing = db.scalar(select(SalesSequenceEnrollment).where(SalesSequenceEnrollment.organization_id == organization_id, SalesSequenceEnrollment.sequence_id == sequence_id, SalesSequenceEnrollment.entity_id == entity_id, SalesSequenceEnrollment.status == "active"))
        if existing is not None: raise V3ConflictError("Record is already enrolled in this sequence")
        owner = owner_user_id or getattr(entity, "assigned_user_id", None) or actor_id
        first = db.scalar(select(SalesSequenceStep).where(SalesSequenceStep.sequence_id == sequence_id).order_by(SalesSequenceStep.position.asc()).limit(1))
        if first is None: raise V3ValidationError("Sequence has no steps")
        enrollment = SalesSequenceEnrollment(organization_id=organization_id, sequence_id=sequence_id, entity_type=sequence.entity_type, entity_id=entity_id, owner_user_id=owner, status="active", next_step_position=0, next_run_at=datetime.now(timezone.utc) + timedelta(days=first.delay_days))
        db.add(enrollment); db.commit(); db.refresh(enrollment); return enrollment

    def list_sequence_enrollments(self, db: Session, organization_id: UUID) -> list[SalesSequenceEnrollment]:
        return list(db.scalars(select(SalesSequenceEnrollment).where(SalesSequenceEnrollment.organization_id == organization_id).order_by(SalesSequenceEnrollment.started_at.desc()).limit(250)))

    def process_due_sequences(self, db: Session, *, limit: int = 50) -> int:
        now = datetime.now(timezone.utc)
        due = list(db.scalars(select(SalesSequenceEnrollment).where(SalesSequenceEnrollment.status == "active", SalesSequenceEnrollment.next_run_at.is_not(None), SalesSequenceEnrollment.next_run_at <= now).order_by(SalesSequenceEnrollment.next_run_at.asc()).limit(limit)))
        processed = 0
        for enrollment in due:
            sequence = db.scalar(select(SalesSequence).where(SalesSequence.id == enrollment.sequence_id, SalesSequence.organization_id == enrollment.organization_id))
            step = db.scalar(select(SalesSequenceStep).where(SalesSequenceStep.sequence_id == enrollment.sequence_id, SalesSequenceStep.position == enrollment.next_step_position))
            if sequence is None or step is None or not sequence.is_active:
                enrollment.status = "paused" if sequence is not None else "failed"; enrollment.next_run_at = None; continue
            try:
                label = self._sequence_entity_label(db, enrollment)
                if step.action_type == "create_task":
                    db.add(Task(organization_id=enrollment.organization_id, assigned_user_id=enrollment.owner_user_id, title=str(step.config.get("title") or f"Follow up: {label}")[:255], description=str(step.config.get("description") or f"Sequence: {sequence.name}")[:20_000], priority=str(step.config.get("priority") or "medium"), status="open", due_date=now))
                elif step.action_type == "notify_owner":
                    db.add(Notification(organization_id=enrollment.organization_id, user_id=enrollment.owner_user_id, type="sequence", title=str(step.config.get("title") or sequence.name)[:255], body=str(step.config.get("body") or f"Sequence step is due for {label}")[:20_000], entity_type=enrollment.entity_type, entity_id=enrollment.entity_id))
                else:
                    raise V3ValidationError("Unsupported sequence action")
                enrollment.next_step_position += 1
                next_step = db.scalar(select(SalesSequenceStep).where(SalesSequenceStep.sequence_id == enrollment.sequence_id, SalesSequenceStep.position == enrollment.next_step_position))
                if next_step is None:
                    enrollment.status = "completed"; enrollment.finished_at = now; enrollment.next_run_at = None
                else:
                    enrollment.next_run_at = now + timedelta(days=next_step.delay_days)
                enrollment.last_error = None; processed += 1
            except Exception as exc:
                enrollment.last_error = str(exc)[:2000]; enrollment.status = "failed"; enrollment.next_run_at = None
        db.commit(); return processed

    def _sequence_entity_label(self, db: Session, enrollment: SalesSequenceEnrollment) -> str:
        entity = self._require_entity(db, enrollment.organization_id, enrollment.entity_type, enrollment.entity_id)
        if enrollment.entity_type == "lead": return str(getattr(entity, "title", entity.id))
        if enrollment.entity_type == "contact": return f"{getattr(entity, 'first_name', '')} {getattr(entity, 'last_name', '')}".strip() or str(entity.id)
        return str(entity.id)

    # ------------------------------ Local AI -------------------------------
    _RECOMMENDED_OLLAMA_MODELS = (
        "gemma3:4b",
        "qwen2.5:3b",
        "llama3.2:3b",
    )

    def ai_status(self) -> AiStatusResponse:
        setup_steps = [
            "Install Ollama from https://ollama.com/download.",
            "Start Ollama, then refresh this page.",
            f"Install a model with: ollama pull {self.settings.ollama_model}",
            "Restart the CRM after changing OLLAMA_MODEL in backend/.env.",
        ]
        if not self.settings.ollama_enabled:
            return AiStatusResponse(available=False, ollama_reachable=False, configured_model_available=False, base_url=self.settings.ollama_base_url, model=self.settings.ollama_model, detail="Local AI is disabled by configuration", setup_steps=setup_steps)
        try:
            response = httpx.get(f"{self.settings.ollama_base_url.rstrip('/')}/api/tags", timeout=min(self.settings.ollama_timeout_seconds, 3.0))
            response.raise_for_status()
            raw_models = response.json().get("models", [])
            installed_models = [
                AiModelResponse(name=name, size_bytes=item.get("size") if isinstance(item.get("size"), int) else None, installed=True)
                for item in raw_models
                if isinstance(item, dict) and isinstance((name := item.get("name")), str) and name.strip()
            ]
            names = {item.name for item in installed_models}
            model_available = self.settings.ollama_model in names or any(str(name).startswith(self.settings.ollama_model.split(":")[0] + ":") for name in names if name)
            recommended_models = [
                AiModelResponse(name=name, installed=name in names, recommended=True)
                for name in dict.fromkeys((self.settings.ollama_model, *self._RECOMMENDED_OLLAMA_MODELS))
            ]
            return AiStatusResponse(available=model_available, ollama_reachable=True, configured_model_available=model_available, base_url=self.settings.ollama_base_url, model=self.settings.ollama_model, detail="Ollama and the configured model are ready" if model_available else "Ollama is reachable, but the configured model is not installed", installed_models=installed_models, recommended_models=recommended_models, setup_steps=setup_steps)
        except Exception:
            return AiStatusResponse(available=False, ollama_reachable=False, configured_model_available=False, base_url=self.settings.ollama_base_url, model=self.settings.ollama_model, detail="Ollama is not reachable on the configured local URL", setup_steps=setup_steps)

    @staticmethod
    def _copilot_system_prompt(language: str) -> str:
        return (
            "You are the Enterprise CRM copilot. You can explain your CRM capabilities, provide practical CRM guidance, "
            "and answer questions about the supplied CRM data. Read-only means you cannot create, edit, or delete records; "
            "it does not mean you must refuse general questions. For data-specific questions, use only the supplied CRM context "
            "and never invent records, amounts, dates, or actions. If the supplied data is insufficient, say exactly what is missing. "
            "Use short, useful answers with Markdown only when it improves readability. "
            f"Answer in {language}."
        )

    @staticmethod
    def _needs_record_context(prompt: str) -> bool:
        normalized = prompt.casefold()
        capability_phrases = (
            "what can you do", "how can you help", "who are you", "what do you do",
            "چه کمکی", "چه کار", "کی هستی", "راهنما", "قابلیت",
        )
        return not any(phrase in normalized for phrase in capability_phrases)

    def ai_copilot(self, db: Session, organization_id: UUID, user_id: UUID, prompt: str, locale: str) -> AiCopilotResponse:
        context = self._ai_context(db, organization_id, user_id, include_records=self._needs_record_context(prompt))
        language = "Persian" if locale == "fa" else "English"
        system = self._copilot_system_prompt(language)
        answer = self._ollama_chat(system, f"CRM context:\n{json.dumps(context, default=str, ensure_ascii=False)}\n\nUser request: {prompt}")
        return AiCopilotResponse(answer=answer, model=self.settings.ollama_model, context_summary=context)

    def build_ai_copilot_stream(self, db: Session, organization_id: UUID, user_id: UUID, prompt: str, locale: str, requested_model: str | None = None) -> Iterator[dict[str, str]]:
        status = self.ai_status()
        model = requested_model or self.settings.ollama_model
        installed = {item.name for item in status.installed_models}
        if not status.ollama_reachable or model not in installed:
            raise V3ExternalServiceError("Ollama or the configured model is not ready")
        context = self._ai_context(db, organization_id, user_id, include_records=self._needs_record_context(prompt))
        language = "Persian" if locale == "fa" else "English"
        system = self._copilot_system_prompt(language)
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": f"CRM context:\n{json.dumps(context, default=str, ensure_ascii=False)}\n\nUser request: {prompt}"},
            ],
            "stream": True,
            "options": {"temperature": 0.1, "num_predict": 220},
            # Supported reasoning models (such as Qwen 3) start answering immediately;
            # models that do not expose this option simply ignore it.
            "think": False,
        }

        def events() -> Iterator[dict[str, str]]:
            try:
                with httpx.stream("POST", f"{self.settings.ollama_base_url.rstrip('/')}/api/chat", json=body, timeout=self.settings.ollama_timeout_seconds) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line:
                            continue
                        payload = json.loads(line)
                        content = payload.get("message", {}).get("content")
                        if isinstance(content, str) and content:
                            yield {"type": "token", "text": content}
                        if payload.get("done") is True:
                            yield {"type": "done", "model": model}
                            return
                yield {"type": "error", "detail": "Local AI returned an incomplete response"}
            except Exception:
                yield {"type": "error", "detail": "Unable to stream a response from the configured local Ollama model"}

        return events()

    def pull_ai_model(self, model: str) -> Iterator[dict[str, str]]:
        if not self.settings.ollama_enabled:
            raise V3ExternalServiceError("Local AI is disabled")
        def events() -> Iterator[dict[str, str]]:
            try:
                with httpx.stream("POST", f"{self.settings.ollama_base_url.rstrip('/')}/api/pull", json={"name": model, "stream": True}, timeout=600.0) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line: continue
                        payload = json.loads(line)
                        yield {"type": "progress", "detail": str(payload.get("status", "Downloading model")), "completed": str(payload.get("completed", 0)), "total": str(payload.get("total", 0))}
                        if payload.get("status") == "success": yield {"type": "done", "model": model}; return
            except Exception:
                yield {"type": "error", "detail": "Unable to download the selected Ollama model"}
        return events()

    def ai_deal_insight(self, db: Session, organization_id: UUID, deal_id: UUID) -> AiDealInsightResponse:
        deal = db.scalar(select(Deal).where(Deal.id == deal_id, Deal.organization_id == organization_id))
        if deal is None: raise V3NotFoundError("Deal not found")
        company = db.scalar(select(Company).where(Company.id == deal.company_id, Company.organization_id == organization_id))
        activities = list(db.scalars(select(Activity).where(Activity.organization_id == organization_id, Activity.company_id == deal.company_id).order_by(Activity.created_at.desc()).limit(8)))
        payload = {
            "deal": {"id": str(deal.id), "title": deal.title, "value": str(deal.value), "currency": deal.currency, "probability": str(deal.probability), "status": deal.status, "expected_close_date": deal.expected_close_date.isoformat(), "updated_at": deal.updated_at.isoformat()},
            "company": company.name if company else None,
            "recent_activities": [{"title": item.title, "type": item.type, "completed": item.completed, "due_date": item.due_date.isoformat() if item.due_date else None} for item in activities],
        }
        schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
                "risk_reasons": {"type": "array", "items": {"type": "string"}},
                "next_actions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["summary", "risk_level", "risk_reasons", "next_actions"],
        }
        raw = self._ollama_chat("You are a CRM deal analyst. Analyze only the supplied data and return the requested JSON schema. Be conservative and never invent facts.", json.dumps(payload, ensure_ascii=False), format_schema=schema)
        try:
            parsed = json.loads(raw)
            return AiDealInsightResponse(deal_id=deal.id, model=self.settings.ollama_model, **parsed)
        except Exception as exc:
            raise V3ExternalServiceError("Local AI returned an invalid structured response") from exc

    def _ai_context(self, db: Session, organization_id: UUID, user_id: UUID, include_records: bool = True) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        # Local models have finite context windows. Sending hundreds of unrelated
        # records makes even a simple question slow and less accurate. The CRM
        # remains the source of truth; this is the focused recent context passed
        # to the model for one answer.
        limit = 50 if include_records else 0
        companies = list(db.scalars(select(Company).where(Company.organization_id == organization_id).order_by(Company.updated_at.desc()).limit(limit)))
        leads = list(db.scalars(select(Lead).where(Lead.organization_id == organization_id).order_by(Lead.updated_at.desc()).limit(limit)))
        deals = list(db.scalars(select(Deal).where(Deal.organization_id == organization_id).order_by(Deal.updated_at.desc()).limit(limit)))
        tasks = list(db.scalars(select(Task).where(Task.organization_id == organization_id).order_by(Task.updated_at.desc()).limit(limit)))
        activities = list(db.scalars(select(Activity).where(Activity.organization_id == organization_id).order_by(Activity.created_at.desc()).limit(limit)))
        notes = list(db.scalars(select(Note).where(Note.organization_id == organization_id).order_by(Note.updated_at.desc()).limit(limit)))
        contacts = list(db.scalars(select(Contact).join(Company).where(Company.organization_id == organization_id).limit(limit)))
        overdue_tasks = [
            task
            for task in tasks
            if task.assigned_user_id == user_id
            and task.status not in ("completed", "cancelled")
            and task.due_date
            and (task.due_date.replace(tzinfo=timezone.utc) if task.due_date.tzinfo is None else task.due_date) < now
        ]
        context = {
            "counts": {
                "companies": int(db.scalar(select(func.count(Company.id)).where(Company.organization_id == organization_id)) or 0),
                "open_leads": int(db.scalar(select(func.count(Lead.id)).where(Lead.organization_id == organization_id, Lead.status.not_in(("converted", "lost")))) or 0),
                "open_deals": int(db.scalar(select(func.count(Deal.id)).where(Deal.organization_id == organization_id, Deal.status == "open")) or 0),
                "my_overdue_tasks": len(overdue_tasks),
            },
            "companies": [{"id": str(item.id), "name": item.name, "industry": item.industry, "website": item.website} for item in companies],
            "contacts": [{"id": str(item.id), "company_id": str(item.company_id), "name": f"{item.first_name} {item.last_name}", "email": item.email, "phone": item.phone} for item in contacts],
            "leads": [{"id": str(item.id), "title": item.title, "status": item.status, "source": item.source, "company_id": str(item.company_id) if item.company_id else None} for item in leads],
            "deals": [{"id": str(item.id), "title": item.title, "value": str(item.value), "currency": item.currency, "probability": str(item.probability), "status": item.status, "close_date": item.expected_close_date.isoformat()} for item in deals],
            "tasks": [{"id": str(item.id), "title": item.title, "status": item.status, "priority": item.priority, "due_date": item.due_date.isoformat() if item.due_date else None} for item in tasks],
            "activities": [{"id": str(item.id), "title": item.title, "type": item.type, "completed": item.completed, "due_date": item.due_date.isoformat() if item.due_date else None} for item in activities],
            "notes": [{"id": str(item.id), "content": item.content[:400] if item.content else None} for item in notes],
            "my_overdue_tasks": [{"id": str(task.id), "title": task.title, "priority": task.priority, "due_date": task.due_date.isoformat() if task.due_date else None} for task in overdue_tasks],
        }
        if not include_records:
            context.update({
                "companies": [], "contacts": [], "leads": [], "deals": [], "tasks": [], "activities": [], "notes": [], "my_overdue_tasks": [],
                "context_note": "No record-level CRM context was needed for this general question.",
            })
        return context

    def _ollama_chat(self, system: str, prompt: str, format_schema: dict[str, Any] | None = None) -> str:
        if not self.settings.ollama_enabled: raise V3ExternalServiceError("Local AI is disabled")
        body: dict[str, Any] = {"model": self.settings.ollama_model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], "stream": False, "options": {"temperature": 0.1}}
        if format_schema is not None: body["format"] = format_schema
        try:
            response = httpx.post(f"{self.settings.ollama_base_url.rstrip('/')}/api/chat", json=body, timeout=self.settings.ollama_timeout_seconds)
            response.raise_for_status()
            content = response.json().get("message", {}).get("content")
            if not isinstance(content, str) or not content.strip(): raise V3ExternalServiceError("Local AI returned an empty response")
            return content.strip()
        except V3ExternalServiceError: raise
        except Exception as exc: raise V3ExternalServiceError("Unable to reach the configured local Ollama model") from exc

    # -------------------------- Developer platform -------------------------
    def list_api_keys(self, db: Session, organization_id: UUID, user_id: UUID) -> list[ApiKey]:
        return list(db.scalars(select(ApiKey).where(ApiKey.organization_id == organization_id, ApiKey.user_id == user_id).order_by(ApiKey.created_at.desc())))

    def create_api_key(self, db: Session, organization_id: UUID, user_id: UUID, data: ApiKeyCreate) -> ApiKeyCreatedResponse:
        if data.expires_at is not None:
            expires = data.expires_at if data.expires_at.tzinfo else data.expires_at.replace(tzinfo=timezone.utc)
            if expires <= datetime.now(timezone.utc): raise V3ValidationError("API key expiry must be in the future")
        prefix = secrets.token_hex(4)
        secret = secrets.token_urlsafe(32)
        token = f"crm_live_{prefix}_{secret}"
        row = ApiKey(organization_id=organization_id, user_id=user_id, name=data.name, prefix=prefix, secret_hash=hashlib.sha256(token.encode()).hexdigest(), expires_at=data.expires_at, is_active=True)
        db.add(row); db.commit(); db.refresh(row)
        return ApiKeyCreatedResponse(id=row.id, name=row.name, prefix=row.prefix, is_active=row.is_active, last_used_at=row.last_used_at, expires_at=row.expires_at, created_at=row.created_at, token=token)

    def revoke_api_key(self, db: Session, organization_id: UUID, user_id: UUID, key_id: UUID) -> None:
        row = db.scalar(select(ApiKey).where(ApiKey.id == key_id, ApiKey.organization_id == organization_id, ApiKey.user_id == user_id))
        if row is None: raise V3NotFoundError("API key not found")
        row.is_active = False; db.commit()

    def authenticate_api_key(self, db: Session, token: str) -> User | None:
        if not token.startswith("crm_live_"): return None
        parts = token.split("_", 3)
        if len(parts) != 4: return None
        prefix = parts[2]
        row = db.scalar(select(ApiKey).where(ApiKey.prefix == prefix, ApiKey.is_active.is_(True)))
        if row is None: return None
        if row.expires_at is not None:
            expires = row.expires_at if row.expires_at.tzinfo else row.expires_at.replace(tzinfo=timezone.utc)
            if expires <= datetime.now(timezone.utc): return None
        digest = hashlib.sha256(token.encode()).hexdigest()
        if not hmac.compare_digest(digest, row.secret_hash): return None
        user = db.scalar(select(User).where(User.id == row.user_id, User.organization_id == row.organization_id, User.is_active.is_(True)))
        if user is not None:
            row.last_used_at = datetime.now(timezone.utc)
            db.commit()
        return user

    def list_webhooks(self, db: Session, organization_id: UUID) -> list[WebhookEndpoint]:
        return list(db.scalars(select(WebhookEndpoint).where(WebhookEndpoint.organization_id == organization_id).order_by(WebhookEndpoint.created_at.desc())))

    def create_webhook(self, db: Session, organization_id: UUID, data: WebhookCreate) -> WebhookCreatedResponse:
        signing_secret = secrets.token_urlsafe(32)
        row = WebhookEndpoint(organization_id=organization_id, name=data.name, url=data.url, events=data.events, is_active=data.is_active, signing_secret=encrypt_secret(signing_secret, self.settings.jwt_secret.get_secret_value()))
        db.add(row)
        db.commit()
        db.refresh(row)
        return WebhookCreatedResponse(
            id=row.id,
            name=row.name,
            url=row.url,
            events=list(row.events or []),
            is_active=row.is_active,
            last_error=row.last_error,
            created_at=row.created_at,
            updated_at=row.updated_at,
            signing_secret=signing_secret,
        )

    def list_webhook_deliveries(self, db: Session, organization_id: UUID, endpoint_id: UUID | None = None) -> list[WebhookDelivery]:
        clauses = [WebhookDelivery.organization_id == organization_id]
        if endpoint_id is not None: clauses.append(WebhookDelivery.endpoint_id == endpoint_id)
        return list(db.scalars(select(WebhookDelivery).where(*clauses).order_by(WebhookDelivery.created_at.desc()).limit(250)))

    def retry_webhook_delivery(self, db: Session, organization_id: UUID, delivery_id: UUID) -> WebhookDelivery:
        delivery = db.scalar(select(WebhookDelivery).where(WebhookDelivery.id == delivery_id, WebhookDelivery.organization_id == organization_id))
        if delivery is None: raise V3NotFoundError("Webhook delivery not found")
        delivery.status = "pending"; delivery.next_attempt_at = datetime.now(timezone.utc); delivery.last_error = None
        db.commit(); db.refresh(delivery); return delivery

    def enqueue_webhook_event(self, db: Session, organization_id: UUID, event_type: str, payload: dict[str, Any]) -> int:
        endpoints = list(db.scalars(select(WebhookEndpoint).where(WebhookEndpoint.organization_id == organization_id, WebhookEndpoint.is_active.is_(True))))
        queued = 0
        safe_payload = self._json_safe(payload)
        for endpoint in endpoints:
            if event_type in (endpoint.events or []) or "*" in (endpoint.events or []):
                db.add(WebhookDelivery(organization_id=organization_id, endpoint_id=endpoint.id, event_type=event_type, payload=safe_payload, status="pending", attempts=0, next_attempt_at=datetime.now(timezone.utc)))
                queued += 1
        return queued

    def process_webhook_deliveries(self, db: Session, *, limit: int = 50) -> int:
        now = datetime.now(timezone.utc)
        deliveries = list(db.scalars(select(WebhookDelivery).where(WebhookDelivery.status.in_(("pending", "retrying")), or_(WebhookDelivery.next_attempt_at.is_(None), WebhookDelivery.next_attempt_at <= now)).order_by(WebhookDelivery.created_at.asc()).limit(limit)))
        processed = 0
        for delivery in deliveries:
            endpoint = db.scalar(select(WebhookEndpoint).where(WebhookEndpoint.id == delivery.endpoint_id, WebhookEndpoint.organization_id == delivery.organization_id, WebhookEndpoint.is_active.is_(True)))
            if endpoint is None:
                delivery.status = "failed"; delivery.last_error = "Webhook endpoint is missing or disabled"; continue
            try:
                self._validate_webhook_destination(endpoint.url)
                envelope = {"id": str(delivery.id), "event": delivery.event_type, "created_at": delivery.created_at.isoformat() if delivery.created_at else now.isoformat(), "data": delivery.payload}
                raw = json.dumps(envelope, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                signing_secret = decrypt_secret(endpoint.signing_secret, self.settings.jwt_secret.get_secret_value())
                signature = hmac.new(signing_secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
                response = httpx.post(endpoint.url, content=raw, headers={"Content-Type": "application/json", "User-Agent": "EnterpriseCRM-Webhook/3.0", "X-CRM-Event": delivery.event_type, "X-CRM-Delivery": str(delivery.id), "X-CRM-Signature": f"sha256={signature}"}, timeout=10.0, follow_redirects=False)
                delivery.attempts += 1; delivery.response_status = response.status_code
                if 200 <= response.status_code < 300:
                    delivery.status = "delivered"; delivery.delivered_at = now; delivery.next_attempt_at = None; delivery.last_error = None; endpoint.last_error = None
                else:
                    raise V3ExternalServiceError(f"Webhook returned HTTP {response.status_code}")
            except Exception as exc:
                delivery.attempts += 1 if delivery.response_status is None else 0
                delivery.last_error = str(exc)[:2000]; endpoint.last_error = delivery.last_error
                if delivery.attempts >= 5:
                    delivery.status = "failed"; delivery.next_attempt_at = None
                else:
                    delivery.status = "retrying"; delivery.next_attempt_at = now + timedelta(minutes=min(60, 2 ** delivery.attempts))
            processed += 1
        db.commit(); return processed

    def _validate_webhook_destination(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise V3ValidationError("Webhook destination must be HTTPS")
        try:
            infos = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise V3ExternalServiceError("Webhook hostname could not be resolved") from exc
        for info in infos:
            ip = ipaddress.ip_address(info[4][0])
            if self.settings.environment == "production" and (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast):
                raise V3ValidationError("Webhook destination resolves to a private or reserved address")

    @staticmethod
    def _json_safe(payload: dict[str, Any]) -> dict[str, Any]:
        return json.loads(json.dumps(payload, default=str, ensure_ascii=False))

    # ------------------------------- Helpers -------------------------------
    def _get_workflow(self, db: Session, organization_id: UUID, workflow_id: UUID) -> Workflow:
        workflow = db.scalar(select(Workflow).where(Workflow.id == workflow_id, Workflow.organization_id == organization_id))
        if workflow is None: raise V3NotFoundError("Workflow not found")
        return workflow

    def _require_entity(self, db: Session, organization_id: UUID, entity_type: str, entity_id: UUID):
        if entity_type == "contact":
            entity = db.scalar(select(Contact).join(Company, Contact.company_id == Company.id).where(Contact.id == entity_id, Company.organization_id == organization_id))
        else:
            model = ENTITY_MODELS.get(entity_type)
            if model is None or not hasattr(model, "organization_id"): raise V3ValidationError("Unsupported entity type")
            entity = db.scalar(select(model).where(model.id == entity_id, model.organization_id == organization_id))
        if entity is None: raise V3NotFoundError(f"{entity_type.title()} not found")
        return entity

    def _entity_snapshot(self, db: Session, organization_id: UUID, entity_type: str, entity_id: UUID) -> dict[str, Any]:
        entity = self._require_entity(db, organization_id, entity_type, entity_id)
        result: dict[str, Any] = {"id": str(entity.id)}
        for key in ENTITY_MUTABLE_FIELDS.get(entity_type, frozenset()):
            value = getattr(entity, key, None)
            if isinstance(value, (UUID, Decimal, datetime, date)): value = str(value)
            result[key] = value
        if hasattr(entity, "assigned_user_id"): result["assigned_user_id"] = str(entity.assigned_user_id)
        return result

    @staticmethod
    def _conditions_match(conditions: list[dict[str, Any]], payload: dict[str, Any]) -> bool:
        for condition in conditions:
            field, operator, expected = condition.get("field"), condition.get("operator"), condition.get("value")
            actual = payload.get(field)
            if operator == "eq" and actual != expected: return False
            if operator == "neq" and actual == expected: return False
            if operator == "contains" and (actual is None or str(expected).lower() not in str(actual).lower()): return False
            if operator == "in" and actual not in (expected or []): return False
            if operator == "is_empty" and actual not in (None, "", [], {}): return False
            if operator == "not_empty" and actual in (None, "", [], {}): return False
            if operator in {"gt", "gte", "lt", "lte"}:
                try: left, right = Decimal(str(actual)), Decimal(str(expected))
                except Exception: return False
                if operator == "gt" and not left > right: return False
                if operator == "gte" and not left >= right: return False
                if operator == "lt" and not left < right: return False
                if operator == "lte" and not left <= right: return False
        return True

    @staticmethod
    def _resolve_workflow_user(raw: Any, actor_id: UUID, payload: dict[str, Any]) -> UUID:
        if raw in (None, "actor"): return actor_id
        if raw == "owner" and payload.get("assigned_user_id"): return UUID(str(payload["assigned_user_id"]))
        return UUID(str(raw))

    @staticmethod
    def _normalize_custom_value(definition: CustomFieldDefinition, value: Any) -> Any:
        if value is None:
            if definition.required: raise V3ValidationError(f"{definition.label} is required")
            return None
        if definition.data_type == "text": return str(value)[:20_000]
        if definition.data_type in {"number", "currency"}:
            try: return float(Decimal(str(value)))
            except Exception as exc: raise V3ValidationError(f"{definition.label} must be numeric") from exc
        if definition.data_type == "boolean":
            if not isinstance(value, bool): raise V3ValidationError(f"{definition.label} must be true or false")
            return value
        if definition.data_type == "date":
            try: return date.fromisoformat(str(value)).isoformat()
            except Exception as exc: raise V3ValidationError(f"{definition.label} must be an ISO date") from exc
        if definition.data_type in {"url", "email"}: return str(value)[:2048]
        if definition.data_type == "select":
            if value not in (definition.options or []): raise V3ValidationError(f"{definition.label} has an invalid option")
            return value
        if definition.data_type == "multi_select":
            if not isinstance(value, list) or any(item not in (definition.options or []) for item in value): raise V3ValidationError(f"{definition.label} has invalid options")
            return value
        return value


v3_platform_service = V3PlatformService(get_settings())
