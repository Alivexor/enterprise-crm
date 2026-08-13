import type { PaginationParams } from "@/types/pagination";

export type Tag = {
  color: string;
  created_at: string;
  id: string;
  name: string;
  organization_id: string;
};

export type TagInput = { color: string; name: string };

export const tagEntityTypes = ["company", "contact", "lead", "deal"] as const;

export type TagEntityType = (typeof tagEntityTypes)[number];

export type TagsListParams = PaginationParams & {
  search?: string;
  sort_by?: "created_at" | "name";
  sort_direction?: "asc" | "desc";
};
