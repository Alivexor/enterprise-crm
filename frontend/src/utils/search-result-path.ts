import type { SearchResult } from "@/types/search";

export function searchResultPath(result: SearchResult): string {
  const routeByType = {
    activity: "activities",
    company: "companies",
    contact: "contacts",
    deal: "deals",
    lead: "leads",
    note: "notes",
    task: "tasks",
  } as const;
  return `/dashboard/${routeByType[result.entity_type]}/${result.id}`;
}
