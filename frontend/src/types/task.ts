import type { PaginationParams } from "@/types/pagination";

export const taskPriorities = ["low", "medium", "high", "urgent"] as const;
export const taskStatuses = ["open", "in_progress", "completed", "cancelled"] as const;

export type TaskPriority = (typeof taskPriorities)[number];
export type TaskStatus = (typeof taskStatuses)[number];

export type Task = {
  assigned_user_id: string;
  created_at: string;
  description: string | null;
  due_date: string | null;
  id: string;
  organization_id: string;
  priority: TaskPriority;
  status: TaskStatus;
  title: string;
  updated_at: string;
};

export type TaskInput = {
  assigned_user_id?: string | null;
  description: string | null;
  due_date: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  title: string;
};

export type TasksListParams = PaginationParams & {
  assigned_user_id?: string;
  search?: string;
  sort_by?: "created_at" | "due_date" | "priority";
  sort_direction?: "asc" | "desc";
  status?: TaskStatus;
};
