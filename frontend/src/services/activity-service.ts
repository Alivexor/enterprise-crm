import { apiClient } from "@/services/api-client";
import type { ActivitiesListParams, Activity, ActivityInput } from "@/types/activity";
import type { PaginatedResponse } from "@/types/pagination";
import { toQueryString } from "@/utils/query-string";

export const activityService = {
  create(activity: ActivityInput): Promise<Activity> {
    return apiClient.post<Activity>("/activities", JSON.stringify(activity));
  },

  get(activityId: string): Promise<Activity> {
    return apiClient.get<Activity>(`/activities/${activityId}`, { cache: "no-store" });
  },

  list(params: ActivitiesListParams = {}): Promise<PaginatedResponse<Activity>> {
    return apiClient.get<PaginatedResponse<Activity>>(
      `/activities${toQueryString(params)}`,
      { cache: "no-store" },
    );
  },

  remove(activityId: string): Promise<void> {
    return apiClient.delete<void>(`/activities/${activityId}`);
  },

  update(activityId: string, activity: Partial<ActivityInput>): Promise<Activity> {
    return apiClient.patch<Activity>(`/activities/${activityId}`, JSON.stringify(activity));
  },
};
