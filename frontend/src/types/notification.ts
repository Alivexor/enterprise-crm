import type { PaginationParams } from "@/types/pagination";

export type NotificationReadState = "all" | "read" | "unread";

export type Notification = {
  body: string | null;
  created_at: string;
  entity_id: string | null;
  entity_type: string | null;
  id: string;
  organization_id: string;
  read_at: string | null;
  title: string;
  type: string;
  user_id: string;
};

export type NotificationsListParams = PaginationParams & {
  read?: NotificationReadState;
};
