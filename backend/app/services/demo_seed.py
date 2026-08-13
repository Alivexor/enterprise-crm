from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.activity import Activity
from app.models.company import Company
from app.models.contact import Contact
from app.models.deal import Deal
from app.models.lead import Lead
from app.models.note import Note
from app.models.notification import Notification
from app.models.permission import Permission
from app.models.pipeline import Pipeline
from app.models.pipeline_stage import PipelineStage
from app.models.role import Role
from app.models.tag import Tag
from app.models.task import Task
from app.models.user import User
from app.models.custom_field import CustomFieldDefinition, CustomFieldValue
from app.models.dashboard import DashboardWidget
from app.models.revenue import Product, Quote, QuoteItem, SalesGoal
from app.models.saved_view import SavedView
from app.models.sequence import SalesSequence, SalesSequenceEnrollment, SalesSequenceStep
from app.models.workflow import Workflow

DEMO_PREFIX = "Demo · "
DEMO_EMAIL_DOMAIN = "showcase.example"
DEMO_PIPELINE_NAMES = (
    f"{DEMO_PREFIX}Enterprise Sales",
    f"{DEMO_PREFIX}Growth & SMB",
)


class DemoSeedConfigurationError(Exception):
    """Raised when demo data cannot be safely created or removed."""


@dataclass(frozen=True)
class DemoSeedResult:
    users: int
    roles: int
    companies: int
    contacts: int
    leads: int
    pipelines: int
    pipeline_stages: int
    deals: int
    tasks: int
    activities: int
    notes: int
    tags: int
    notifications: int
    saved_views: int = 0
    custom_fields: int = 0
    workflows: int = 0
    goals: int = 0
    products: int = 0
    quotes: int = 0
    dashboard_widgets: int = 0
    sequences: int = 0
    sequence_enrollments: int = 0


class DemoDataService:
    """Create and remove deterministic development-only portfolio data.

    The showcase dataset is intentionally dense so the CRM looks like a lived-in
    product on first open. All generated records are easy to identify and the
    seeder is idempotent: rerunning it only fills missing demo records.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def seed(self, session: Session) -> DemoSeedResult:
        self._require_development()
        admin = self._get_admin(session)
        organization_id = admin.organization_id
        now = datetime.now(timezone.utc)

        roles = self._ensure_demo_roles(session, organization_id)
        users = self._ensure_demo_users(session, organization_id, admin, roles)
        owners = [admin, *users.values()]

        tag_specs = (
            ("Strategic", "#4F46E5"), ("Expansion", "#0EA5E9"),
            ("Priority", "#F97316"), ("VIP", "#E11D48"),
            ("Renewal", "#14B8A6"), ("Partner", "#8B5CF6"),
            ("Iran Market", "#22C55E"), ("Enterprise", "#2563EB"),
            ("At Risk", "#DC2626"), ("Fast Track", "#F59E0B"),
        )
        tags = {
            name: self._get_or_create_tag(session, organization_id, f"{DEMO_PREFIX}{name}", color)
            for name, color in tag_specs
        }

        company_specs = (
            ("Northstar Labs", "https://northstar.example", "Technology"),
            ("Atlas Manufacturing", "https://atlas.example", "Manufacturing"),
            ("Meridian Health", "https://meridian.example", "Healthcare"),
            ("Cobalt Retail", "https://cobalt.example", "Retail"),
            ("Aurora Fintech", "https://aurora.example", "Financial Services"),
            ("Summit Logistics", "https://summit.example", "Logistics"),
            ("Nova Foods", "https://novafoods.example", "Food & Beverage"),
            ("Beacon Energy", "https://beacon.example", "Energy"),
            ("Harbor Media", "https://harbor.example", "Media"),
            ("Vertex Security", "https://vertex.example", "Cybersecurity"),
            ("Greenline Mobility", "https://greenline.example", "Mobility"),
            ("Orbit Cloud", "https://orbit.example", "Cloud Services"),
            ("داده‌پرداز آریا", "https://arya.example", "فناوری اطلاعات"),
            ("سلامت نوین", "https://novinhealth.example", "سلامت"),
            ("همراه تجارت پارس", "https://parstrade.example", "تجارت الکترونیک"),
            ("انرژی سپهر", "https://sepehr.example", "انرژی"),
            ("لجستیک راهکار", "https://rahkar.example", "لجستیک"),
            ("آموزش آینده", "https://ayandeh.example", "آموزش"),
            ("فروشگاه هرمس", "https://hermes.example", "خرده‌فروشی"),
            ("صنعت کاوه", "https://kaveh.example", "تولید"),
            ("پرداخت مهر", "https://mehrpay.example", "فین‌تک"),
            ("ساخت‌وساز البرز", "https://alborzbuild.example", "ساخت‌وساز"),
            ("هتل آفتاب", "https://aftabhotel.example", "گردشگری"),
            ("بیمه نگین", "https://negin.example", "بیمه"),
        )
        companies = [
            self._get_or_create_company(session, organization_id, f"{DEMO_PREFIX}{name}", website, industry)
            for name, website, industry in company_specs
        ]
        for index, company in enumerate(companies):
            self._append_unique(company.tags, tags[("Strategic", "Expansion", "Priority", "VIP", "Renewal", "Partner", "Iran Market", "Enterprise")[index % 8]])
            if index % 7 == 0:
                self._append_unique(company.tags, tags["Fast Track"])
            if index in (8, 19):
                self._append_unique(company.tags, tags["At Risk"])

        contacts: list[Contact] = []
        english_names = (
            ("Sara", "Morgan"), ("David", "Chen"), ("Olivia", "Brooks"),
            ("Leo", "Grant"), ("Emma", "Wilson"), ("Noah", "Miller"),
            ("Sophia", "Taylor"), ("James", "Anderson"), ("Maya", "Patel"),
            ("Daniel", "Kim"), ("Ava", "Martin"), ("Ethan", "Clark"),
        )
        persian_names = (
            ("مینا", "رحیمی"), ("علی", "کاظمی"), ("سارا", "محمدی"),
            ("رضا", "احمدی"), ("نگار", "حسینی"), ("امیر", "مرادی"),
            ("پریسا", "اکبری"), ("محمد", "صادقی"), ("نازنین", "کریمی"),
            ("آرمان", "جعفری"), ("الهام", "رضایی"), ("کیان", "نوری"),
        )
        for index, company in enumerate(companies):
            first, last = english_names[index % len(english_names)] if index < 12 else persian_names[index % len(persian_names)]
            local = f"contact{index + 1:02d}"
            contacts.append(self._get_or_create_contact(session, company, first, last, f"{local}@demo.example", f"+1 555 200 {1000 + index}" if index < 12 else f"+98 21 4400 {2000 + index}"))
            if index % 2 == 0:
                first2, last2 = english_names[(index + 5) % len(english_names)] if index < 12 else persian_names[(index + 5) % len(persian_names)]
                contacts.append(self._get_or_create_contact(session, company, first2, last2, f"{local}.team@demo.example", f"+1 555 300 {1000 + index}" if index < 12 else f"+98 21 5500 {2000 + index}"))

        enterprise_pipeline = self._get_or_create_pipeline(session, organization_id, DEMO_PIPELINE_NAMES[0], "Complex B2B opportunities and strategic accounts")
        growth_pipeline = self._get_or_create_pipeline(session, organization_id, DEMO_PIPELINE_NAMES[1], "High-velocity growth and mid-market sales")
        stage_specs = (
            (1, "Discovery", Decimal("15")),
            (2, "Qualified", Decimal("35")),
            (3, "Solution fit", Decimal("55")),
            (4, "Negotiation", Decimal("80")),
            (5, "Closed won", Decimal("100")),
        )
        enterprise_stages = {order: self._get_or_create_stage(session, enterprise_pipeline, order, name, probability) for order, name, probability in stage_specs}
        growth_stages = {order: self._get_or_create_stage(session, growth_pipeline, order, name, probability) for order, name, probability in stage_specs}

        lead_titles = (
            "Enterprise analytics expansion", "Operations modernization", "Regional rollout", "Customer intelligence", "Fraud monitoring program",
            "Warehouse automation", "Demand forecasting", "Energy reporting platform", "Creator analytics workspace", "SOC workflow consolidation",
            "Fleet optimization", "Cloud cost governance", "پلتفرم تحلیل داده سازمانی", "پرونده سلامت شعب", "باشگاه مشتریان هوشمند", "سامانه پایش انرژی",
            "بهینه‌سازی زنجیره تامین", "سامانه آموزش سازمانی", "تحلیل رفتار مشتری", "اتوماسیون خط تولید", "داشبورد مدیریت پرداخت", "مدیریت پروژه‌های ساخت", "سامانه وفاداری مهمانان", "مدیریت خسارت دیجیتال",
            "Executive reporting upgrade", "Customer success workspace", "Data governance initiative", "AI-assisted service desk", "سامانه گزارش‌گیری مدیریتی", "مدیریت فروش چند شعبه", "اتوماسیون خدمات مشتریان", "یکپارچه‌سازی داده‌های مالی",
        )
        lead_statuses = ("new", "qualified", "qualified", "converted", "lost", "unqualified")
        lead_sources = ("website", "referral", "event", "outbound", "advertising", "other")
        leads: list[Lead] = []
        for index, title in enumerate(lead_titles):
            company = companies[index % len(companies)]
            contact = next(c for c in contacts if c.company_id == company.id)
            owner = owners[index % len(owners)]
            lead = self._get_or_create_lead(session, organization_id, owner, title, company, contact, lead_sources[index % len(lead_sources)], lead_statuses[index % len(lead_statuses)])
            self._append_unique(lead.tags, tags[("Priority", "Strategic", "Expansion", "Fast Track")[index % 4]])
            leads.append(lead)

        deal_titles = (
            "Northstar enterprise expansion", "Atlas automation platform", "Meridian regional rollout", "Cobalt customer intelligence", "Aurora risk analytics",
            "Summit logistics control tower", "Nova demand planning", "Beacon sustainability suite", "Harbor audience intelligence", "Vertex security operations",
            "Greenline fleet optimization", "Orbit cloud governance", "آریا داده‌محور ۳۶۰", "سلامت نوین - استقرار منطقه‌ای", "پارس - باشگاه مشتریان", "سپهر - داشبورد انرژی",
            "راهکار - کنترل عملیات", "آینده - پلتفرم آموزش", "هرمس - تحلیل فروش", "کاوه - اتوماسیون تولید", "مهر - تحلیل تراکنش", "البرز - مدیریت پروژه", "آفتاب - تجربه مشتری", "نگین - مدیریت خسارت",
            "Northstar data workspace renewal", "Atlas pilot renewal", "Aurora compliance add-on", "Orbit enterprise support", "Meridian analytics extension", "Vertex incident intelligence",
            "پرداخت مهر - فاز دوم", "فروشگاه هرمس - توسعه شعب", "بیمه نگین - پورتال نمایندگان", "صنعت کاوه - نگهداری پیش‌بینانه",
        )
        deals: list[Deal] = []
        for index, title in enumerate(deal_titles):
            company = companies[index % len(companies)]
            contact = next(c for c in contacts if c.company_id == company.id)
            pipeline = enterprise_pipeline if index % 3 != 1 else growth_pipeline
            stages = enterprise_stages if pipeline is enterprise_pipeline else growth_stages
            if index in (4, 12, 21, 28):
                status, stage_order, close_offset = "lost", 4, -10 - index
            elif index in (8, 16, 24, 30, 33):
                status, stage_order, close_offset = "won", 5, -5 - index
            else:
                status, stage_order, close_offset = "open", (index % 4) + 1, 7 + (index * 3) % 95
            value = Decimal(str(18000 + ((index * 17300) % 245000)))
            deal = self._get_or_create_deal(session, organization_id, owners[(index + 1) % len(owners)], pipeline, stages[stage_order], f"{DEMO_PREFIX}{title}", company, contact, value, status, date.today() + timedelta(days=close_offset))
            self._append_unique(deal.tags, tags[("Enterprise", "Strategic", "Priority", "Renewal", "Fast Track")[index % 5]])
            deals.append(deal)

        task_titles = (
            "Prepare executive proposal", "Review security questionnaire", "Confirm stakeholder map", "Draft discovery agenda", "Update account plan",
            "Validate pricing assumptions", "Prepare ROI model", "Schedule technical workshop", "Review legal redlines", "Confirm procurement timeline",
            "Create implementation brief", "Update opportunity forecast", "Call dormant account", "Prepare renewal deck", "Check product usage signals",
            "Follow up on demo feedback", "Finalize architecture diagram", "Send case study pack", "Prepare QBR summary", "Review integration scope",
            "تهیه پیشنهاد مالی", "پیگیری جلسه مدیرعامل", "تکمیل نقشه ذی‌نفعان", "ارسال مستندات فنی", "بررسی شرایط قرارداد",
            "هماهنگی جلسه دمو", "تکمیل گزارش هفتگی فروش", "پیگیری تایید واحد حقوقی", "آماده‌سازی برنامه استقرار", "بررسی نیازمندی‌های امنیتی",
            "ارسال نمونه گزارش مدیریتی", "پیگیری تمدید قرارداد", "مرور وضعیت فرصت‌های کلیدی", "به‌روزرسانی پیش‌بینی فروش", "برنامه‌ریزی جلسه موفقیت مشتری",
            "Resolve onboarding blocker", "Refresh board notes", "Prepare partner briefing", "Review at-risk accounts", "Plan next-month pipeline review",
        )
        tasks: list[Task] = []
        for index, title in enumerate(task_titles):
            status = ("open", "in_progress", "open", "completed", "open", "cancelled")[index % 6]
            priority = ("urgent", "high", "medium", "low")[index % 4]
            due_offset = (-4, -1, 0, 1, 2, 4, 7, 12, 20)[index % 9]
            tasks.append(self._get_or_create_task(session, organization_id, owners[index % len(owners)], f"{DEMO_PREFIX}{title}", priority, status, now + timedelta(days=due_offset, hours=index % 8)))

        activity_titles = (
            "Executive proposal review", "Technical follow-up", "Procurement call", "Discovery notes", "Success check-in", "Architecture workshop",
            "Pricing review", "Legal follow-up", "Security review meeting", "Product demo", "Integration planning", "Renewal discussion",
            "جلسه بررسی نیازمندی‌ها", "تماس پیگیری پیشنهاد", "ارسال مستندات فنی", "جلسه با واحد فناوری", "پیگیری قرارداد", "جلسه معرفی محصول",
            "بررسی سناریوی استقرار", "تماس با مدیر پروژه", "ارسال گزارش تحلیلی", "جلسه برنامه‌ریزی فاز دوم", "پیگیری تایید مالی", "جلسه هماهنگی تیم فروش",
            "Executive sponsor sync", "Solution engineering call", "Commercial review", "Partner alignment", "Account health review", "Forecast calibration",
            "Customer reference call", "Implementation readiness", "Business case review", "Data migration workshop", "Quarterly planning", "Stakeholder interview",
            "Competitive review", "Expansion planning", "Renewal risk review", "Training planning", "Outcome review", "Final negotiation sync",
        )
        activities: list[Activity] = []
        for index, title in enumerate(activity_titles):
            company = companies[index % len(companies)]
            contact = next(c for c in contacts if c.company_id == company.id)
            lead = leads[index % len(leads)] if index % 5 != 4 else None
            completed = index % 5 == 0
            due_offset = (-7, -2, -1, 0, 1, 2, 3, 5, 8, 14)[index % 10]
            activities.append(self._get_or_create_activity(session, organization_id, owners[(index + 2) % len(owners)], f"{DEMO_PREFIX}{title}", ("meeting", "follow_up", "call", "email")[index % 4], company, contact, lead, now + timedelta(days=due_offset, hours=index % 6), completed))

        note_templates = (
            "Executive sponsor wants measurable adoption KPIs and a phased rollout plan.",
            "Security review is the main dependency before the solution workshop.",
            "Procurement requested a clear implementation timeline and ownership model.",
            "Customer is comparing two vendors; differentiation should focus on analytics depth.",
            "Budget is approved, but legal redlines must close before month end.",
            "Champion is highly engaged and asked for customer references in the same industry.",
            "تیم مشتری روی سرعت استقرار و گزارش‌های مدیریتی تاکید دارد.",
            "تصمیم‌گیرنده اصلی درخواست کرده نمونه داشبورد با داده واقعی‌نما ارائه شود.",
            "واحد فناوری نیازمند مستندات امنیتی و معماری دقیق‌تر است.",
            "مشتری برای فاز اول بودجه دارد و در صورت موفقیت، توسعه سراسری انجام می‌شود.",
        )
        notes: list[Note] = []
        for index in range(30):
            lead = leads[index % len(leads)]
            company = next(c for c in companies if c.id == lead.company_id)
            contact = next(c for c in contacts if c.id == lead.contact_id)
            content = f"{DEMO_PREFIX}{note_templates[index % len(note_templates)]} [Account insight {index + 1:02d}]"
            notes.append(self._get_or_create_note(session, organization_id, owners[(index + 3) % len(owners)], company, contact, lead, content))

        notifications: list[Notification] = []
        notification_specs = (
            ("deal_moved", "Deal moved to Negotiation", "Northstar enterprise expansion is now in Negotiation."),
            ("task_due", "Task due today", "Review the Atlas security questionnaire before the technical workshop."),
            ("lead_assigned", "New qualified lead", "Meridian multi-site rollout has been assigned to your team."),
            ("mention", "You were mentioned in a note", "A teammate mentioned you on the Cobalt account."),
            ("renewal", "Renewal window opened", "Northstar data workspace renewal is entering its renewal window."),
            ("risk", "At-risk account detected", "Harbor Media has had no completed activity in the last two weeks."),
            ("forecast", "Forecast updated", "This month's weighted pipeline increased by 12%."),
            ("meeting", "Meeting in 2 hours", "Executive proposal review starts in two hours."),
            ("task_due", "۳ کار برای امروز", "سه فعالیت مهم در برنامه امروز شما قرار دارد."),
            ("deal_moved", "فرصت فروش وارد مذاکره شد", "فرصت پرداخت مهر وارد مرحله مذاکره شده است."),
            ("lead_assigned", "سرنخ جدید", "یک سرنخ جدید از کانال وب‌سایت به شما تخصیص داده شد."),
            ("risk", "هشدار حساب پرریسک", "حساب صنعت کاوه نیازمند پیگیری فوری است."),
            ("success", "Customer milestone reached", "Meridian completed the solution-fit milestone."),
            ("import", "Import completed", "24 contact records were imported successfully."),
            ("system", "Weekly CRM digest ready", "Your portfolio pipeline, activity, and task summary is ready."),
            ("deal_won", "Deal won 🎉", "Northstar data workspace renewal was marked as won."),
            ("activity", "Follow-up completed", "The Vertex security review follow-up was completed."),
            ("system", "دموی CRM آماده است", "داده‌های نمایشی برای ارائه نمونه‌کار با موفقیت آماده شدند."),
        )
        for index, (kind, title, body) in enumerate(notification_specs):
            read_at = now - timedelta(hours=index + 1) if index % 3 == 0 else None
            notifications.append(self._get_or_create_notification(session, organization_id, admin, kind, f"{DEMO_PREFIX}{title}", f"{DEMO_PREFIX}{body}", read_at))

        v3 = self._ensure_v3_showcase(
            session, organization_id=organization_id, admin=admin, companies=companies,
            contacts=contacts, leads=leads, deals=deals, now=now,
        )
        session.commit()
        return DemoSeedResult(
            users=len(users), roles=len(roles), companies=len(companies), contacts=len(contacts), leads=len(leads),
            pipelines=2, pipeline_stages=len(enterprise_stages) + len(growth_stages), deals=len(deals), tasks=len(tasks),
            activities=len(activities), notes=len(notes), tags=len(tags), notifications=len(notifications),
            **v3,
        )

    def clear(self, session: Session) -> DemoSeedResult:
        self._require_development()
        admin = self._get_admin(session)
        organization_id = admin.organization_id

        v3 = self._clear_v3_showcase(session, organization_id=organization_id)

        notification_count = self._delete_prefixed(session, Notification, organization_id=organization_id, field=Notification.title)
        activity_count = self._delete_prefixed(session, Activity, organization_id=organization_id, field=Activity.title)
        note_count = self._delete_prefixed(session, Note, organization_id=organization_id, field=Note.content)
        lead_count = self._delete_prefixed(session, Lead, organization_id=organization_id, field=Lead.title)
        deal_count = self._delete_prefixed(session, Deal, organization_id=organization_id, field=Deal.title)
        task_count = self._delete_prefixed(session, Task, organization_id=organization_id, field=Task.title)

        contacts = session.scalars(select(Contact).join(Company).where(
            Company.organization_id == organization_id,
            Company.name.like(f"{DEMO_PREFIX}%"),
        )).all()
        contact_count = len(contacts)
        for contact in contacts:
            session.delete(contact)
        session.flush()

        pipelines = session.scalars(select(Pipeline).where(
            Pipeline.organization_id == organization_id,
            Pipeline.name.like(f"{DEMO_PREFIX}%"),
        )).all()
        pipeline_count = len(pipelines)
        stage_count = sum(len(pipeline.stages) for pipeline in pipelines)
        for pipeline in pipelines:
            session.delete(pipeline)
        session.flush()

        companies = session.scalars(select(Company).where(
            Company.organization_id == organization_id,
            Company.name.like(f"{DEMO_PREFIX}%"),
        )).all()
        company_count = len(companies)
        for company in companies:
            session.delete(company)
        session.flush()

        tag_count = self._delete_prefixed(session, Tag, organization_id=organization_id, field=Tag.name)

        demo_users = session.scalars(select(User).where(
            User.organization_id == organization_id,
            User.email.like(f"%@{DEMO_EMAIL_DOMAIN}"),
        )).all()
        user_count = len(demo_users)
        for user in demo_users:
            session.delete(user)
        session.flush()

        demo_roles = session.scalars(select(Role).where(
            Role.organization_id == organization_id,
            Role.name.like(f"{DEMO_PREFIX}%"),
        )).all()
        role_count = len(demo_roles)
        for role in demo_roles:
            session.delete(role)
        session.flush()

        session.commit()
        return DemoSeedResult(
            users=user_count, roles=role_count, companies=company_count, contacts=contact_count, leads=lead_count,
            pipelines=pipeline_count, pipeline_stages=stage_count, deals=deal_count, tasks=task_count,
            activities=activity_count, notes=note_count, tags=tag_count, notifications=notification_count,
            **v3,
        )

    def _ensure_v3_showcase(self, session: Session, *, organization_id, admin: User, companies: list[Company], contacts: list[Contact], leads: list[Lead], deals: list[Deal], now: datetime) -> dict[str, int]:
        # Saved views
        view_specs = (
            ("High-value pipeline", "deals", {"status": "open", "min_value": 50000}, "value", "desc", True),
            ("My stale leads", "leads", {"status": "qualified", "assigned_to_me": True}, "updated_at", "asc", False),
            ("Overdue follow-ups", "tasks", {"status": "todo", "overdue": True}, "due_date", "asc", True),
        )
        views: list[SavedView] = []
        for name, resource, filters, sort_by, direction, shared in view_specs:
            full_name = f"{DEMO_PREFIX}{name}"
            row = session.scalar(select(SavedView).where(SavedView.organization_id == organization_id, SavedView.user_id == admin.id, SavedView.resource == resource, SavedView.name == full_name))
            if row is None:
                row = SavedView(organization_id=organization_id, user_id=admin.id, name=full_name, resource=resource, filters=filters, sort_by=sort_by, sort_direction=direction, is_shared=shared)
                session.add(row); session.flush()
            views.append(row)

        # Custom fields + values make record details visibly extensible.
        field_specs = (
            ("company", "demo_account_tier", "Demo · Account tier", "select", ["Strategic", "Growth", "Standard"]),
            ("company", "demo_renewal_month", "Demo · Renewal month", "text", None),
            ("lead", "demo_budget_confirmed", "Demo · Budget confirmed", "boolean", None),
            ("deal", "demo_competitor", "Demo · Primary competitor", "text", None),
        )
        definitions: list[CustomFieldDefinition] = []
        for position, (entity_type, key, label, data_type, options) in enumerate(field_specs):
            row = session.scalar(select(CustomFieldDefinition).where(CustomFieldDefinition.organization_id == organization_id, CustomFieldDefinition.entity_type == entity_type, CustomFieldDefinition.field_key == key))
            if row is None:
                row = CustomFieldDefinition(organization_id=organization_id, entity_type=entity_type, field_key=key, label=label, data_type=data_type, required=False, options=options, position=position, is_active=True)
                session.add(row); session.flush()
            definitions.append(row)
        demo_values = [
            (definitions[0], companies[0].id, "Strategic"), (definitions[0], companies[1].id, "Growth"),
            (definitions[1], companies[0].id, "October"), (definitions[2], leads[0].id, True),
            (definitions[3], deals[0].id, "Legacy incumbent"),
        ]
        for definition, entity_id, value in demo_values:
            row = session.scalar(select(CustomFieldValue).where(CustomFieldValue.definition_id == definition.id, CustomFieldValue.entity_id == entity_id))
            if row is None:
                session.add(CustomFieldValue(organization_id=organization_id, definition_id=definition.id, entity_id=entity_id, value=value, updated_by_user_id=admin.id))

        workflow_specs = (
            ("High-value opportunity guardrail", "deal", "deal.updated", [{"field": "probability", "operator": "gte", "value": 70}], [{"type": "create_task", "config": {"title": "Demo · Prepare executive close plan", "priority": "high", "assigned_user_id": "owner", "due_days": 2}}]),
            ("Qualified lead follow-up", "lead", "lead.updated", [{"field": "status", "operator": "eq", "value": "qualified"}], [{"type": "create_task", "config": {"title": "Demo · Contact newly qualified lead", "priority": "high", "assigned_user_id": "owner", "due_days": 1}}]),
            ("Urgent task visibility", "task", "task.updated", [{"field": "priority", "operator": "eq", "value": "urgent"}], [{"type": "notify_user", "config": {"title": "Urgent task", "message": "An urgent showcase task needs attention.", "user": "actor"}}]),
        )
        workflows: list[Workflow] = []
        for name, entity_type, event_type, conditions, actions in workflow_specs:
            full_name=f"{DEMO_PREFIX}{name}"
            row=session.scalar(select(Workflow).where(Workflow.organization_id==organization_id, Workflow.name==full_name))
            if row is None:
                row=Workflow(organization_id=organization_id,name=full_name,description="Portfolio showcase automation — safe to edit or delete.",entity_type=entity_type,event_type=event_type,conditions=conditions,actions=actions,is_active=True)
                session.add(row); session.flush()
            workflows.append(row)

        goal_specs=(
            ("Quarterly won revenue", "won_revenue", Decimal("950000"), "USD", date.today()-timedelta(days=30), date.today()+timedelta(days=60)),
            ("New pipeline coverage", "pipeline_value", Decimal("1800000"), "USD", date.today()-timedelta(days=15), date.today()+timedelta(days=75)),
            ("Qualified lead target", "qualified_leads", Decimal("45"), None, date.today().replace(day=1), date.today()+timedelta(days=30)),
        )
        goals: list[SalesGoal]=[]
        for name, metric, target, currency, start, end in goal_specs:
            full_name=f"{DEMO_PREFIX}{name}"
            row=session.scalar(select(SalesGoal).where(SalesGoal.organization_id==organization_id, SalesGoal.name==full_name))
            if row is None:
                row=SalesGoal(organization_id=organization_id,user_id=None,name=full_name,metric=metric,target_value=target,currency=currency,start_date=start,end_date=end)
                session.add(row); session.flush()
            goals.append(row)

        product_specs=(
            ("CRM Enterprise Platform", "DEMO-CRM-ENT", Decimal("24000")),
            ("Analytics & Forecasting Add-on", "DEMO-ANL-01", Decimal("8500")),
            ("Implementation Sprint", "DEMO-IMP-01", Decimal("12000")),
            ("Premium Success", "DEMO-CS-01", Decimal("6000")),
        )
        products: list[Product]=[]
        for name, sku, price in product_specs:
            row=session.scalar(select(Product).where(Product.organization_id==organization_id, Product.sku==sku))
            if row is None:
                row=Product(organization_id=organization_id,name=f"{DEMO_PREFIX}{name}",sku=sku,description="Showcase catalog item",unit_price=price,currency="USD",is_active=True)
                session.add(row); session.flush()
            products.append(row)

        quote_specs=(
            ("DEMO-Q-3001", deals[0], companies[0], contacts[0], Decimal("10"), "draft"),
            ("DEMO-Q-3002", deals[1], companies[1], contacts[1], Decimal("25"), "pending_approval"),
            ("DEMO-Q-3003", deals[2], companies[2], contacts[2], Decimal("5"), "approved"),
        )
        quotes: list[Quote]=[]
        for idx,(number,deal,company,contact,discount,status_value) in enumerate(quote_specs):
            row=session.scalar(select(Quote).where(Quote.organization_id==organization_id, Quote.quote_number==number))
            if row is None:
                row=Quote(organization_id=organization_id,deal_id=deal.id,company_id=company.id,contact_id=contact.id,owner_user_id=admin.id,quote_number=number,status=status_value,currency="USD",discount_percent=discount,tax_percent=Decimal("5"),valid_until=date.today()+timedelta(days=21+idx*7),notes=f"{DEMO_PREFIX}Portfolio quote with realistic approval state.")
                if status_value=="approved": row.approved_by_user_id=admin.id; row.approved_at=now; row.approval_note="Demo · Approved for portfolio showcase"
                session.add(row); session.flush()
                line_products=products[:2] if idx!=2 else products[1:4]
                for position,product in enumerate(line_products):
                    session.add(QuoteItem(organization_id=organization_id,quote_id=row.id,product_id=product.id,description=product.name,quantity=Decimal("1"),unit_price=product.unit_price,position=position))
            quotes.append(row)

        widget_specs=(
            ("Demo · CRM health", "data_quality", {}, 0),
            ("Demo · Revenue forecast", "forecast", {}, 1),
            ("Demo · Deals by status", "report", {"resource":"deals","metric":"count","group_by":"status"}, 2),
            ("Demo · Quarterly target", "goal", {"goal_id":str(goals[0].id)}, 3),
        )
        widgets: list[DashboardWidget]=[]
        for title,widget_type,config,position in widget_specs:
            row=session.scalar(select(DashboardWidget).where(DashboardWidget.organization_id==organization_id, DashboardWidget.user_id==admin.id, DashboardWidget.title==title))
            if row is None:
                row=DashboardWidget(organization_id=organization_id,user_id=admin.id,title=title,widget_type=widget_type,config=config,position=position)
                session.add(row); session.flush()
            widgets.append(row)

        sequence_specs=(
            ("New lead 5-day cadence", "lead", [(0,"create_task",{"title":"Demo · Review lead context","priority":"high"}),(2,"notify_owner",{"title":"Demo · Follow-up checkpoint","body":"Two days passed — review engagement."}),(5,"create_task",{"title":"Demo · Final qualification touch","priority":"medium"})]),
            ("Deal momentum cadence", "deal", [(0,"create_task",{"title":"Demo · Confirm next step","priority":"high"}),(3,"notify_owner",{"title":"Demo · Deal momentum","body":"Check whether the opportunity needs a new action."})]),
        )
        sequences: list[SalesSequence]=[]; enrollment_count=0
        for seq_index,(name,entity_type,steps) in enumerate(sequence_specs):
            full_name=f"{DEMO_PREFIX}{name}"
            seq=session.scalar(select(SalesSequence).where(SalesSequence.organization_id==organization_id, SalesSequence.name==full_name))
            if seq is None:
                seq=SalesSequence(organization_id=organization_id,name=full_name,description="Showcase follow-up cadence processed by the local worker.",entity_type=entity_type,is_active=True)
                session.add(seq); session.flush()
                for position,(delay,action_type,config) in enumerate(steps): session.add(SalesSequenceStep(organization_id=organization_id,sequence_id=seq.id,position=position,delay_days=delay,action_type=action_type,config=config))
                session.flush()
            sequences.append(seq)
            targets=leads[:2] if entity_type=="lead" else deals[:2]
            for offset,target in enumerate(targets):
                existing=session.scalar(select(SalesSequenceEnrollment).where(SalesSequenceEnrollment.organization_id==organization_id, SalesSequenceEnrollment.sequence_id==seq.id, SalesSequenceEnrollment.entity_id==target.id))
                if existing is None:
                    session.add(SalesSequenceEnrollment(organization_id=organization_id,sequence_id=seq.id,entity_type=entity_type,entity_id=target.id,owner_user_id=admin.id,status="active",next_step_position=0,next_run_at=now+timedelta(hours=offset+1)))
                enrollment_count += 1

        session.flush()
        return {
            "saved_views": len(views), "custom_fields": len(definitions), "workflows": len(workflows),
            "goals": len(goals), "products": len(products), "quotes": len(quotes),
            "dashboard_widgets": len(widgets), "sequences": len(sequences), "sequence_enrollments": enrollment_count,
        }

    def _clear_v3_showcase(self, session: Session, *, organization_id) -> dict[str, int]:
        sequences=session.scalars(select(SalesSequence).where(SalesSequence.organization_id==organization_id, SalesSequence.name.like(f"{DEMO_PREFIX}%"))).all()
        sequence_ids=[row.id for row in sequences]
        enrollments=session.scalars(select(SalesSequenceEnrollment).where(SalesSequenceEnrollment.organization_id==organization_id, SalesSequenceEnrollment.sequence_id.in_(sequence_ids))).all() if sequence_ids else []
        for row in enrollments: session.delete(row)
        session.flush()
        for row in sequences: session.delete(row)
        session.flush()

        widgets=session.scalars(select(DashboardWidget).where(DashboardWidget.organization_id==organization_id, DashboardWidget.title.like(f"{DEMO_PREFIX}%"))).all()
        for row in widgets: session.delete(row)
        quotes=session.scalars(select(Quote).where(Quote.organization_id==organization_id, Quote.quote_number.like("DEMO-Q-%"))).all()
        for row in quotes: session.delete(row)
        products=session.scalars(select(Product).where(Product.organization_id==organization_id, Product.sku.like("DEMO-%"))).all()
        for row in products: session.delete(row)
        goals=session.scalars(select(SalesGoal).where(SalesGoal.organization_id==organization_id, SalesGoal.name.like(f"{DEMO_PREFIX}%"))).all()
        for row in goals: session.delete(row)
        workflows=session.scalars(select(Workflow).where(Workflow.organization_id==organization_id, Workflow.name.like(f"{DEMO_PREFIX}%"))).all()
        for row in workflows: session.delete(row)
        fields=session.scalars(select(CustomFieldDefinition).where(CustomFieldDefinition.organization_id==organization_id, CustomFieldDefinition.field_key.like("demo_%"))).all()
        for row in fields: session.delete(row)
        views=session.scalars(select(SavedView).where(SavedView.organization_id==organization_id, SavedView.name.like(f"{DEMO_PREFIX}%"))).all()
        for row in views: session.delete(row)
        session.flush()
        return {
            "saved_views":len(views), "custom_fields":len(fields), "workflows":len(workflows), "goals":len(goals),
            "products":len(products), "quotes":len(quotes), "dashboard_widgets":len(widgets),
            "sequences":len(sequences), "sequence_enrollments":len(enrollments),
        }

    def _require_development(self) -> None:
        if self.settings.environment != "development":
            raise DemoSeedConfigurationError("Demo data is only available when ENVIRONMENT=development")

    def _get_admin(self, session: Session) -> User:
        email = str(self.settings.default_admin_email).lower()
        admin = session.scalar(select(User).where(
            User.organization_id == self.settings.default_organization_id,
            User.email == email,
        ))
        if admin is None:
            raise DemoSeedConfigurationError("Development admin is missing; run the development seed first")
        return admin

    def _ensure_demo_roles(self, session: Session, organization_id) -> dict[str, Role]:
        permissions = {permission.name: permission for permission in session.scalars(select(Permission)).all()}
        role_specs = {
            "Sales Manager": ("dashboard.read", "analytics.read", "search.read", "companies.read", "contacts.read", "leads.read", "leads.create", "leads.update", "pipelines.read", "deals.read", "deals.create", "deals.update", "activities.read", "activities.create", "activities.update", "tasks.read", "tasks.create", "tasks.update", "notes.read", "notes.create", "tags.read", "notifications.read", "notifications.update", "profile.read"),
            "Account Executive": ("dashboard.read", "search.read", "companies.read", "contacts.read", "leads.read", "leads.create", "leads.update", "pipelines.read", "deals.read", "deals.create", "deals.update", "activities.read", "activities.create", "activities.update", "tasks.read", "tasks.create", "tasks.update", "notes.read", "notes.create", "tags.read", "notifications.read", "notifications.update", "profile.read"),
            "Customer Success": ("dashboard.read", "search.read", "companies.read", "contacts.read", "deals.read", "activities.read", "activities.create", "activities.update", "tasks.read", "tasks.create", "tasks.update", "notes.read", "notes.create", "notifications.read", "notifications.update", "profile.read"),
        }
        result: dict[str, Role] = {}
        for role_name, permission_names in role_specs.items():
            full_name = f"{DEMO_PREFIX}{role_name}"
            role = session.scalar(select(Role).where(Role.organization_id == organization_id, Role.name == full_name))
            if role is None:
                role = Role(organization_id=organization_id, name=full_name)
                session.add(role)
                session.flush()
            for permission_name in permission_names:
                permission = permissions.get(permission_name)
                if permission is not None and permission not in role.permissions:
                    role.permissions.append(permission)
            result[role_name] = role
        return result

    def _ensure_demo_users(self, session: Session, organization_id, admin: User, roles: dict[str, Role]) -> dict[str, User]:
        specs = (
            ("nina.rahimi", "Nina", "Rahimi", "Sales Manager"),
            ("sam.wilson", "Sam", "Wilson", "Account Executive"),
            ("parsa.karimi", "Parsa", "Karimi", "Account Executive"),
            ("leila.moradi", "Leila", "Moradi", "Customer Success"),
            ("emma.clark", "Emma", "Clark", "Customer Success"),
        )
        result: dict[str, User] = {}
        for local, first_name, last_name, role_name in specs:
            email = f"{local}@{DEMO_EMAIL_DOMAIN}"
            user = session.scalar(select(User).where(User.organization_id == organization_id, User.email == email))
            if user is None:
                user = User(
                    organization_id=organization_id,
                    email=email,
                    password_hash=admin.password_hash,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                )
                session.add(user)
                session.flush()
            role = roles[role_name]
            self._append_unique(user.roles, role)
            result[local] = user
        return result

    @staticmethod
    def _append_unique(collection: list, item: object) -> None:
        if item not in collection:
            collection.append(item)

    @staticmethod
    def _get_or_create_tag(session: Session, organization_id, name: str, color: str) -> Tag:
        item = session.scalar(select(Tag).where(Tag.organization_id == organization_id, Tag.name == name))
        if item is None:
            item = Tag(organization_id=organization_id, name=name, color=color)
            session.add(item)
            session.flush()
        return item

    @staticmethod
    def _get_or_create_company(session: Session, organization_id, name: str, website: str, industry: str) -> Company:
        item = session.scalar(select(Company).where(Company.organization_id == organization_id, Company.name == name))
        if item is None:
            item = Company(organization_id=organization_id, name=name, website=website, industry=industry)
            session.add(item)
            session.flush()
        return item

    @staticmethod
    def _get_or_create_contact(session: Session, company: Company, first_name: str, last_name: str, email: str, phone: str) -> Contact:
        item = session.scalar(select(Contact).where(Contact.company_id == company.id, Contact.email == email))
        if item is None:
            item = Contact(company_id=company.id, first_name=first_name, last_name=last_name, email=email, phone=phone)
            session.add(item)
            session.flush()
        return item

    @staticmethod
    def _get_or_create_pipeline(session: Session, organization_id, name: str, description: str) -> Pipeline:
        item = session.scalar(select(Pipeline).where(Pipeline.organization_id == organization_id, Pipeline.name == name))
        if item is None:
            item = Pipeline(organization_id=organization_id, name=name, description=description)
            session.add(item)
            session.flush()
        return item

    @staticmethod
    def _get_or_create_stage(session: Session, pipeline: Pipeline, order: int, name: str, probability: Decimal) -> PipelineStage:
        item = session.scalar(select(PipelineStage).where(PipelineStage.pipeline_id == pipeline.id, PipelineStage.order == order))
        if item is None:
            item = PipelineStage(pipeline_id=pipeline.id, order=order, name=name, probability=probability)
            session.add(item)
            session.flush()
        return item

    @staticmethod
    def _get_or_create_lead(session: Session, organization_id, owner: User, title: str, company: Company, contact: Contact, source: str, status: str) -> Lead:
        full_title = f"{DEMO_PREFIX}{title}"
        item = session.scalar(select(Lead).where(Lead.organization_id == organization_id, Lead.title == full_title))
        if item is None:
            description = "Portfolio showcase lead with realistic account context." if not any("\u0600" <= ch <= "\u06FF" for ch in title) else "سرنخ نمایشی برای نمونه‌کار با اطلاعات واقع‌گرایانه مشتری."
            item = Lead(organization_id=organization_id, company_id=company.id, contact_id=contact.id, title=full_title, description=description, source=source, status=status, assigned_user_id=owner.id)
            session.add(item)
            session.flush()
        return item

    @staticmethod
    def _get_or_create_deal(session: Session, organization_id, owner: User, pipeline: Pipeline, stage: PipelineStage, title: str, company: Company, contact: Contact, value: Decimal, status: str, close_date: date) -> Deal:
        item = session.scalar(select(Deal).where(Deal.organization_id == organization_id, Deal.title == title))
        if item is None:
            item = Deal(organization_id=organization_id, company_id=company.id, contact_id=contact.id, pipeline_id=pipeline.id, stage_id=stage.id, assigned_user_id=owner.id, title=title, value=value, currency="USD", probability=stage.probability, expected_close_date=close_date, status=status)
            session.add(item)
            session.flush()
        return item

    @staticmethod
    def _get_or_create_task(session: Session, organization_id, owner: User, title: str, priority: str, status: str, due_date: datetime) -> Task:
        item = session.scalar(select(Task).where(Task.organization_id == organization_id, Task.title == title))
        if item is None:
            description = "Showcase task generated for a realistic portfolio workspace." if not any("\u0600" <= ch <= "\u06FF" for ch in title) else "وظیفه نمایشی برای نمایش یک محیط کاری واقعی و پرمحتوا."
            item = Task(organization_id=organization_id, assigned_user_id=owner.id, title=title, description=description, priority=priority, status=status, due_date=due_date)
            session.add(item)
            session.flush()
        return item

    @staticmethod
    def _get_or_create_activity(session: Session, organization_id, owner: User, title: str, kind: str, company: Company, contact: Contact, lead: Lead | None, due_date: datetime, completed: bool) -> Activity:
        item = session.scalar(select(Activity).where(Activity.organization_id == organization_id, Activity.title == title))
        if item is None:
            description = "Showcase customer interaction with account context and follow-up." if not any("\u0600" <= ch <= "\u06FF" for ch in title) else "تعامل نمایشی با مشتری همراه با جزئیات و پیگیری بعدی."
            item = Activity(organization_id=organization_id, user_id=owner.id, company_id=company.id, contact_id=contact.id, lead_id=lead.id if lead else None, type=kind, title=title, description=description, due_date=due_date, completed=completed)
            session.add(item)
            session.flush()
        return item

    @staticmethod
    def _get_or_create_note(session: Session, organization_id, owner: User, company: Company, contact: Contact, lead: Lead, content: str) -> Note:
        item = session.scalar(select(Note).where(Note.organization_id == organization_id, Note.content == content))
        if item is None:
            item = Note(organization_id=organization_id, user_id=owner.id, company_id=company.id, contact_id=contact.id, lead_id=lead.id, content=content)
            session.add(item)
            session.flush()
        return item

    @staticmethod
    def _get_or_create_notification(session: Session, organization_id, user: User, kind: str, title: str, body: str, read_at: datetime | None) -> Notification:
        item = session.scalar(select(Notification).where(Notification.organization_id == organization_id, Notification.user_id == user.id, Notification.title == title))
        if item is None:
            item = Notification(organization_id=organization_id, user_id=user.id, type=kind, title=title, body=body, read_at=read_at)
            session.add(item)
            session.flush()
        return item

    @staticmethod
    def _delete_prefixed(session: Session, model, *, organization_id, field) -> int:
        items = session.scalars(select(model).where(model.organization_id == organization_id, field.like(f"{DEMO_PREFIX}%"))).all()
        count = len(items)
        for item in items:
            session.delete(item)
        session.flush()
        return count
