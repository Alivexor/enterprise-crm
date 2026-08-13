import type { Deal } from "@/types/deal";
import type { PaginationParams } from "@/types/pagination";

export const leadSources = [
  "advertising",
  "event",
  "outbound",
  "referral",
  "website",
  "other",
] as const;

export const leadStatuses = ["new", "qualified", "unqualified", "converted", "lost"] as const;

export type LeadSource = (typeof leadSources)[number];
export type LeadStatus = (typeof leadStatuses)[number];

export type Lead = {
  assigned_user_id: string;
  company_id: string | null;
  contact_id: string | null;
  created_at: string;
  description: string | null;
  id: string;
  organization_id: string;
  source: LeadSource;
  status: LeadStatus;
  title: string;
  updated_at: string;
};

export type LeadInput = {
  assigned_user_id?: string | null;
  company_id: string | null;
  contact_id: string | null;
  description: string | null;
  source: LeadSource;
  status: LeadStatus;
  title: string;
};

export type LeadsListParams = PaginationParams & {
  assigned_user_id?: string;
  company_id?: string;
  search?: string;
  sort_by?: "created_at" | "status" | "title";
  sort_direction?: "asc" | "desc";
  status?: LeadStatus;
};

export type LeadConversionInput = {
  currency: string;
  expected_close_date: string;
  pipeline_id: string;
  probability: number;
  stage_id: string;
  title?: string | null;
  value: number;
};

export type LeadConversionResult = {
  deal: Deal;
  lead: Lead;
};
