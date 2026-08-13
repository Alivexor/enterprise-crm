import { apiClient } from "@/services/api-client";
import type { AuditLog, AuditLogsListParams } from "@/types/audit-log";
import type { PaginatedResponse } from "@/types/pagination";
import { toQueryString } from "@/utils/query-string";

export const auditLogService = {
  list(params: AuditLogsListParams = {}): Promise<PaginatedResponse<AuditLog>> { return apiClient.get<PaginatedResponse<AuditLog>>(`/audit-logs${toQueryString(params)}`, { cache: "no-store" }); },
};
