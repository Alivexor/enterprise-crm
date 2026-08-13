export type SavedView = {
  id: string;
  user_id: string;
  name: string;
  resource: "companies" | "contacts" | "leads" | "deals" | "tasks" | "activities";
  filters: Record<string, unknown>;
  sort_by: string | null;
  sort_direction: "asc" | "desc";
  is_shared: boolean;
  created_at: string;
  updated_at: string;
};

export type CustomFieldDefinition = {
  id: string;
  entity_type: "company" | "contact" | "lead" | "deal";
  field_key: string;
  label: string;
  data_type: "text" | "number" | "currency" | "date" | "boolean" | "select" | "multi_select" | "url" | "email";
  required: boolean;
  options: string[] | null;
  position: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type WorkflowCondition = {
  field: string;
  operator: "eq" | "neq" | "contains" | "gt" | "gte" | "lt" | "lte" | "in" | "is_empty" | "not_empty";
  value?: unknown;
};

export type WorkflowAction = {
  type: "create_task" | "notify_user" | "set_field";
  config: Record<string, unknown>;
};

export type Workflow = {
  id: string;
  name: string;
  description: string | null;
  entity_type: "lead" | "deal" | "task" | "company";
  event_type: string;
  conditions: WorkflowCondition[];
  actions: WorkflowAction[];
  is_active: boolean;
  run_count: number;
  last_run_at: string | null;
  created_at: string;
  updated_at: string;
};

export type DataQualityIssue = {
  code: string;
  severity: "low" | "medium" | "high";
  title: string;
  count: number;
  resource: string;
  sample_ids: string[];
};

export type DataQuality = {
  score: number;
  total_issues: number;
  issues: DataQualityIssue[];
};

export type ForecastBucket = {
  label: string;
  deal_count: number;
  total_value: string;
  weighted_value: string;
};

export type RevenueForecast = {
  currency: string | null;
  open_pipeline: string;
  weighted_pipeline: string;
  won_revenue: string;
  commit: string;
  best_case: string;
  pipeline: string;
  buckets: ForecastBucket[];
  currency_breakdown: Array<{
    currency: string;
    open_pipeline: string;
    weighted_pipeline: string;
    won_revenue: string;
    commit: string;
    best_case: string;
  }>;
};

export type ReportRow = { label: string; value: string; count: number };
export type ReportBuilderResult = { resource: string; metric: string; group_by: string; rows: ReportRow[]; total: string };

export type SalesGoal = {
  id: string;
  user_id: string | null;
  name: string;
  metric: string;
  target_value: string;
  currency: string | null;
  start_date: string;
  end_date: string;
  current_value: string;
  progress_percent: string;
  created_at: string;
};

export type Product = {
  id: string;
  name: string;
  sku: string;
  description: string | null;
  unit_price: string;
  currency: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type QuoteItem = {
  id: string;
  product_id: string | null;
  description: string;
  quantity: string;
  unit_price: string;
  line_total: string;
};

export type Quote = {
  id: string;
  deal_id: string | null;
  company_id: string;
  contact_id: string | null;
  owner_user_id: string;
  quote_number: string;
  status: string;
  currency: string;
  discount_percent: string;
  tax_percent: string;
  valid_until: string | null;
  notes: string | null;
  approved_by_user_id: string | null;
  approved_at: string | null;
  approval_note: string | null;
  subtotal: string;
  discount_total: string;
  tax_total: string;
  grand_total: string;
  items: QuoteItem[];
  created_at: string;
  updated_at: string;
};

export type RelationshipHealth = {
  company_id: string;
  score: number;
  label: string;
  last_activity_at: string | null;
  activities_30d: number;
  open_deals: number;
  open_deal_value: string;
  overdue_tasks: number;
  factors: string[];
};

export type AiStatus = {
  available: boolean;
  ollama_reachable: boolean;
  configured_model_available: boolean;
  base_url: string;
  model: string;
  detail: string;
  installed_models: AiModel[];
  recommended_models: AiModel[];
  setup_steps: string[];
};

export type AiModel = {
  name: string;
  size_bytes: number | null;
  installed: boolean;
  recommended: boolean;
};

export type AiCopilotResponse = {
  answer: string;
  model: string;
  context_summary: Record<string, unknown>;
};

export type AiDealInsight = {
  deal_id: string;
  summary: string;
  risk_level: "low" | "medium" | "high";
  risk_reasons: string[];
  next_actions: string[];
  model: string;
};

export type ApiKey = {
  id: string;
  name: string;
  prefix: string;
  is_active: boolean;
  last_used_at: string | null;
  expires_at: string | null;
  created_at: string;
};

export type ApiKeyCreated = ApiKey & { token: string };

export type WebhookEndpoint = {
  id: string;
  name: string;
  url: string;
  events: string[];
  is_active: boolean;
  last_error: string | null;
  created_at: string;
  updated_at: string;
};

export type WebhookCreated = WebhookEndpoint & { signing_secret: string };

export type DashboardWidget = {
  id: string;
  title: string;
  widget_type: "report" | "forecast" | "data_quality" | "goal";
  config: Record<string, unknown>;
  position: number;
  created_at: string;
  updated_at: string;
};

export type SequenceStep = {
  id?: string;
  position?: number;
  delay_days: number;
  action_type: "create_task" | "notify_owner";
  config: Record<string, unknown>;
};

export type SalesSequence = {
  id: string;
  name: string;
  description: string | null;
  entity_type: "lead" | "contact";
  is_active: boolean;
  steps: SequenceStep[];
  enrollment_count: number;
  created_at: string;
  updated_at: string;
};

export type SequenceEnrollment = {
  id: string;
  sequence_id: string;
  entity_type: "lead" | "contact";
  entity_id: string;
  owner_user_id: string;
  status: string;
  next_step_position: number;
  next_run_at: string | null;
  started_at: string;
  finished_at: string | null;
  last_error: string | null;
};

export type WebhookDelivery = {
  id: string;
  endpoint_id: string;
  event_type: string;
  status: string;
  attempts: number;
  response_status: number | null;
  last_error: string | null;
  delivered_at: string | null;
  created_at: string;
};

export type AttentionItem = {
  kind: "task" | "deal" | "lead" | "activity";
  entity_id: string;
  title: string;
  reason: string;
  priority: "low" | "medium" | "high";
  route: string;
};

export type MorningBrief = {
  generated_at: string;
  overdue_tasks: number;
  due_today: number;
  stale_leads: number;
  closing_soon_deals: number;
  actions: AttentionItem[];
};

export type LeadScore = {
  lead_id: string;
  score: number;
  grade: "A" | "B" | "C" | "D";
  factors: string[];
  next_actions: string[];
};

export type WinLossAnalytics = {
  won_count: number;
  lost_count: number;
  open_count: number;
  win_rate: string;
  won_value_by_currency: Record<string, string>;
  lost_value_by_currency: Record<string, string>;
  average_won_value_by_currency: Record<string, string>;
};
