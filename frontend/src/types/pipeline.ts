import type { PaginationParams } from "@/types/pagination";

export type PipelineStage = {
  created_at: string;
  id: string;
  name: string;
  order: number;
  pipeline_id: string;
  probability: string | number;
};

export type Pipeline = {
  created_at: string;
  description: string | null;
  id: string;
  name: string;
  organization_id: string;
  updated_at: string;
};

export type PipelineDetail = Pipeline & { stages: PipelineStage[] };

export type PipelineInput = { description: string | null; name: string };
export type PipelineStageInput = { name: string; order: number; probability: number };

export type PipelinesListParams = PaginationParams & {
  search?: string;
  sort_by?: "created_at" | "name" | "updated_at";
  sort_direction?: "asc" | "desc";
};
