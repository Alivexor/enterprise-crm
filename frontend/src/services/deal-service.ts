import { apiClient } from "@/services/api-client";
import type { Deal, DealInput, DealsListParams } from "@/types/deal";
import type { PaginatedResponse } from "@/types/pagination";
import { toQueryString } from "@/utils/query-string";

export const dealService = {
  create(input: DealInput): Promise<Deal> { return apiClient.post<Deal>("/deals", JSON.stringify(input)); },
  get(dealId: string): Promise<Deal> { return apiClient.get<Deal>(`/deals/${dealId}`, { cache: "no-store" }); },
  list(params: DealsListParams = {}): Promise<PaginatedResponse<Deal>> { return apiClient.get<PaginatedResponse<Deal>>(`/deals${toQueryString(params)}`, { cache: "no-store" }); },
  remove(dealId: string): Promise<void> { return apiClient.delete<void>(`/deals/${dealId}`); },
  update(dealId: string, input: Partial<DealInput>): Promise<Deal> { return apiClient.patch<Deal>(`/deals/${dealId}`, JSON.stringify(input)); },
};
