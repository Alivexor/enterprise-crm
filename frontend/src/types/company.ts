export type Company = {
  id: string;
  organization_id: string;
  name: string;
  website: string | null;
  industry: string | null;
  created_at: string;
  updated_at: string;
};

export type CompanyInput = {
  name: string;
  website: string | null;
  industry: string | null;
};

export type CompaniesListParams = {
  industry?: string;
  page?: number;
  page_size?: number;
  search?: string;
  sort_by?: "created_at" | "industry" | "name" | "updated_at";
  sort_direction?: "asc" | "desc";
};
