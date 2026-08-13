import type { PaginationParams } from "@/types/pagination";

export const activityTypes = ["call", "email", "meeting", "follow_up"] as const;

export type ActivityType = (typeof activityTypes)[number];

export type Activity = {
  company_id: string | null;
  completed: boolean;
  contact_id: string | null;
  created_at: string;
  description: string | null;
  due_date: string | null;
  id: string;
  lead_id: string | null;
  organization_id: string;
  title: string;
  type: ActivityType;
  user_id: string;
};

export type ActivityInput = {
  company_id: string | null;
  completed: boolean;
  contact_id: string | null;
  description: string | null;
  due_date: string | null;
  lead_id: string | null;
  title: string;
  type: ActivityType;
  user_id?: string | null;
};

export type ActivitiesListParams = PaginationParams & {
  completed?: boolean;
  company_id?: string;
  contact_id?: string;
  lead_id?: string;
  sort_by?: "created_at" | "due_date" | "type";
  sort_direction?: "asc" | "desc";
  type?: ActivityType;
  user_id?: string;
};
