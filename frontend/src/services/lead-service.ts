import { apiClient } from "@/services/api-client";
import type { Lead, LeadConversionInput, LeadConversionResult, LeadInput, LeadsListParams } from "@/types/lead";
import type { PaginatedResponse } from "@/types/pagination";
import { toQueryString } from "@/utils/query-string";

export const leadService = {
  create(lead: LeadInput): Promise<Lead> {
    return apiClient.post<Lead>("/leads", JSON.stringify(lead));
  },

  convert(leadId: string, input: LeadConversionInput): Promise<LeadConversionResult> {
    return apiClient.post<LeadConversionResult>(`/leads/${leadId}/convert`, JSON.stringify(input));
  },

  get(leadId: string): Promise<Lead> {
    return apiClient.get<Lead>(`/leads/${leadId}`, { cache: "no-store" });
  },

  list(params: LeadsListParams = {}): Promise<PaginatedResponse<Lead>> {
    return apiClient.get<PaginatedResponse<Lead>>(
      `/leads${toQueryString(params)}`,
      { cache: "no-store" },
    );
  },

  remove(leadId: string): Promise<void> {
    return apiClient.delete<void>(`/leads/${leadId}`);
  },

  update(leadId: string, lead: Partial<LeadInput>): Promise<Lead> {
    return apiClient.patch<Lead>(`/leads/${leadId}`, JSON.stringify(lead));
  },
};
