import { apiClient } from "@/services/api-client";
import type {
  Attachment,
  AttachmentEntityType,
  AttachmentListParams,
} from "@/types/attachment";
import type { PaginatedResponse } from "@/types/pagination";
import { toQueryString } from "@/utils/query-string";

export const attachmentService = {
  downloadPath(attachmentId: string): string {
    return `/api/attachments/${attachmentId}/download`;
  },

  list(params: AttachmentListParams): Promise<PaginatedResponse<Attachment>> {
    return apiClient.get<PaginatedResponse<Attachment>>(
      `/attachments${toQueryString(params)}`,
      { cache: "no-store" },
    );
  },

  remove(attachmentId: string): Promise<void> {
    return apiClient.delete<void>(`/attachments/${attachmentId}`);
  },

  upload(
    entityType: AttachmentEntityType,
    entityId: string,
    file: File,
  ): Promise<Attachment> {
    const formData = new FormData();
    formData.set("entity_type", entityType);
    formData.set("entity_id", entityId);
    formData.set("file", file);
    return apiClient.post<Attachment>("/attachments", formData);
  },
};
