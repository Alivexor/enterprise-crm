import type { PaginationParams } from "@/types/pagination";

export type Contact = {
  company_id: string;
  email: string | null;
  first_name: string;
  id: string;
  last_name: string;
  phone: string | null;
};

export type ContactInput = {
  company_id: string;
  email: string | null;
  first_name: string;
  last_name: string;
  phone: string | null;
};

export type ContactsListParams = PaginationParams & {
  company_id?: string;
  search?: string;
  sort_by?: "email" | "first_name" | "last_name";
  sort_direction?: "asc" | "desc";
};
