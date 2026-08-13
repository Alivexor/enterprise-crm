export type DashboardMetric = {
  label: string;
  value: number | string;
};

export type DashboardTask = {
  due_date: string | null;
  id: string;
  priority: string;
  title: string;
};

export type DashboardActivity = {
  due_date: string | null;
  id: string;
  title: string;
  type: string;
};

export type DashboardData = {
  metrics: DashboardMetric[];
  open_tasks: DashboardTask[];
  upcoming_activities: DashboardActivity[];
};

export type PipelineAnalyticsItem = {
  deal_count: number;
  pipeline_id: string;
  pipeline_name: string;
  stage_id: string;
  stage_name: string;
  total_value: number | string;
};

export type StatusAnalyticsItem = {
  count: number;
  status: string;
  total_value: number | string | null;
};

export type AnalyticsData = {
  deals_by_status: StatusAnalyticsItem[];
  leads_by_status: StatusAnalyticsItem[];
  pipeline: PipelineAnalyticsItem[];
};


export type OperationalHealth = {
  activities_next_7_days: number;
  lead_conversion_rate: number | string;
  open_pipeline_value: number | string;
  overdue_tasks: number;
  stale_deals: number;
  stale_leads: number;
  tasks_due_today: number;
  weighted_pipeline_value: number | string;
  won_deal_value: number | string;
};
