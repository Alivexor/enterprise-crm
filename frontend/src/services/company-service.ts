import { apiClient } from "@/services/api-client";
import type { CompaniesListParams, Company, CompanyInput } from "@/types/company";
import type { PaginatedResponse } from "@/types/pagination";
import { toQueryString } from "@/utils/query-string";

export const companyService = {
  create(company: CompanyInput): Promise<Company> {
    return apiClient.post<Company>("/companies", JSON.stringify(company));
  },

  list(params: CompaniesListParams = {}): Promise<PaginatedResponse<Company>> {
    return apiClient.get<PaginatedResponse<Company>>(
      `/companies${toQueryString(params)}`,
      { cache: "no-store" },
    );
  },

  get(companyId: string): Promise<Company> {
    return apiClient.get<Company>(`/companies/${companyId}`, { cache: "no-store" });
  },

  update(companyId: string, company: Partial<CompanyInput>): Promise<Company> {
    return apiClient.patch<Company>(
      `/companies/${companyId}`,
      JSON.stringify(company),
    );
  },

  remove(companyId: string): Promise<void> {
    return apiClient.delete<void>(`/companies/${companyId}`);
  },
};
