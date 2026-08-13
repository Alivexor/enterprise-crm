import type { PaginationParams } from "@/types/pagination";

export const attachmentEntityTypes = [
  "company",
  "contact",
  "lead",
  "deal",
  "activity",
  "task",
  "note",
] as const;

export type AttachmentEntityType = (typeof attachmentEntityTypes)[number];

export type Attachment = {
  content_type: string;
  created_at: string;
  entity_id: string;
  entity_type: AttachmentEntityType;
  id: string;
  organization_id: string;
  original_filename: string;
  size_bytes: number;
  uploaded_by_user_id: string;
};

export type AttachmentListParams = PaginationParams & {
  entity_id: string;
  entity_type: AttachmentEntityType;
};
