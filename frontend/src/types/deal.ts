import type { PaginationParams } from "@/types/pagination";

export const dealStatuses = ["open", "won", "lost"] as const;
export type DealStatus = (typeof dealStatuses)[number];

export type Deal = {
  assigned_user_id: string;
  company_id: string;
  contact_id: string | null;
  created_at: string;
  currency: string;
  expected_close_date: string;
  id: string;
  organization_id: string;
  pipeline_id: string;
  probability: string | number;
  stage_id: string;
  status: DealStatus;
  title: string;
  updated_at: string;
  value: string | number;
};

export type DealInput = {
  assigned_user_id: string;
  company_id: string;
  contact_id: string | null;
  currency: string;
  expected_close_date: string;
  pipeline_id: string;
  probability: number;
  stage_id: string;
  status: DealStatus;
  title: string;
  value: number;
};

export type DealsListParams = PaginationParams & {
  company_id?: string;
  pipeline_id?: string;
  search?: string;
  sort_by?: "created_at" | "expected_close_date" | "probability" | "title" | "updated_at" | "value";
  sort_direction?: "asc" | "desc";
  stage_id?: string;
  status?: DealStatus;
};
