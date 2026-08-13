import type { PaginationParams } from "@/types/pagination";

export type AuditActor = {
  email: string;
  first_name: string;
  id: string;
  last_name: string;
};

export type AuditLog = {
  action: string;
  created_at: string;
  entity_id: string;
  entity_type: string;
  id: string;
  user: AuditActor;
};

export type AuditLogsListParams = PaginationParams & {
  action?: string;
  entity_type?: string;
  search?: string;
  sort_direction?: "asc" | "desc";
};
