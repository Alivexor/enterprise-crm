import { apiClient } from "@/services/api-client";
import type { PaginatedResponse } from "@/types/pagination";
import type {
  Tag,
  TagEntityType,
  TagInput,
  TagsListParams,
} from "@/types/tag";
import { toQueryString } from "@/utils/query-string";

export const tagService = {
  assign(
    tagId: string,
    entityType: TagEntityType,
    entityId: string,
  ): Promise<void> {
    return apiClient.put<void>(
      `/tags/${tagId}/assignments/${entityType}/${entityId}`,
    );
  },
  create(input: TagInput): Promise<Tag> { return apiClient.post<Tag>("/tags", JSON.stringify(input)); },
  get(tagId: string): Promise<Tag> { return apiClient.get<Tag>(`/tags/${tagId}`, { cache: "no-store" }); },
  list(params: TagsListParams = {}): Promise<PaginatedResponse<Tag>> { return apiClient.get<PaginatedResponse<Tag>>(`/tags${toQueryString(params)}`, { cache: "no-store" }); },
  remove(tagId: string): Promise<void> { return apiClient.delete<void>(`/tags/${tagId}`); },
  update(tagId: string, input: Partial<TagInput>): Promise<Tag> { return apiClient.patch<Tag>(`/tags/${tagId}`, JSON.stringify(input)); },
  unassign(
    tagId: string,
    entityType: TagEntityType,
    entityId: string,
  ): Promise<void> {
    return apiClient.delete<void>(
      `/tags/${tagId}/assignments/${entityType}/${entityId}`,
    );
  },
};
