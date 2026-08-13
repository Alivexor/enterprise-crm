import { apiClient } from "@/services/api-client";
import type { Task, TaskInput, TasksListParams } from "@/types/task";
import type { PaginatedResponse } from "@/types/pagination";
import { toQueryString } from "@/utils/query-string";

export const taskService = {
  create(task: TaskInput): Promise<Task> {
    return apiClient.post<Task>("/tasks", JSON.stringify(task));
  },

  get(taskId: string): Promise<Task> {
    return apiClient.get<Task>(`/tasks/${taskId}`, { cache: "no-store" });
  },

  list(params: TasksListParams = {}): Promise<PaginatedResponse<Task>> {
    return apiClient.get<PaginatedResponse<Task>>(
      `/tasks${toQueryString(params)}`,
      { cache: "no-store" },
    );
  },

  remove(taskId: string): Promise<void> {
    return apiClient.delete<void>(`/tasks/${taskId}`);
  },

  update(taskId: string, task: Partial<TaskInput>): Promise<Task> {
    return apiClient.patch<Task>(`/tasks/${taskId}`, JSON.stringify(task));
  },
};
