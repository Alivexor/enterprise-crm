export type SearchEntityType =
  | "activity"
  | "company"
  | "contact"
  | "deal"
  | "lead"
  | "note"
  | "task";

export type SearchResult = {
  entity_type: SearchEntityType;
  id: string;
  subtitle: string | null;
  title: string;
};

export type SearchResponse = { items: SearchResult[] };
