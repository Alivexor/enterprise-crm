import { apiClient } from "@/services/api-client";
import type { Notification, NotificationsListParams } from "@/types/notification";
import type { PaginatedResponse } from "@/types/pagination";
import { toQueryString } from "@/utils/query-string";

export const notificationService = {
  list(params: NotificationsListParams = {}): Promise<PaginatedResponse<Notification>> {
    return apiClient.get<PaginatedResponse<Notification>>(
      `/notifications${toQueryString(params)}`,
      { cache: "no-store" },
    );
  },

  markAllRead(): Promise<void> {
    return apiClient.post<void>("/notifications/read-all");
  },

  markBulkRead(notificationIds: string[]): Promise<{ updated: number }> {
    return apiClient.post<{ updated: number }>(
      "/notifications/read-bulk",
      JSON.stringify({ notification_ids: notificationIds }),
    );
  },

  markRead(notificationId: string): Promise<Notification> {
    return apiClient.post<Notification>(`/notifications/${notificationId}/read`);
  },
};
