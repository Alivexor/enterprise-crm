import type { PaginationParams } from "@/types/pagination";

export type Note = {
  company_id: string | null;
  contact_id: string | null;
  content: string;
  created_at: string;
  id: string;
  lead_id: string | null;
  organization_id: string;
  updated_at: string;
  user_id: string;
};

export type NoteInput = {
  company_id: string | null;
  contact_id: string | null;
  content: string;
  lead_id: string | null;
};

export type NotesListParams = PaginationParams & {
  company_id?: string;
  lead_id?: string;
  search?: string;
  sort_by?: "created_at" | "updated_at";
  sort_direction?: "asc" | "desc";
};
