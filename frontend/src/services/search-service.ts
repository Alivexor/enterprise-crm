import { apiClient } from "@/services/api-client";
import type { SearchResponse } from "@/types/search";
import { toQueryString } from "@/utils/query-string";

export const searchService = {
  search(query: string): Promise<SearchResponse> { return apiClient.get<SearchResponse>(`/search${toQueryString({ limit_per_type: 10, q: query })}`, { cache: "no-store" }); },
};
