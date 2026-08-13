import { apiClient } from "@/services/api-client";
import type { PaginatedResponse } from "@/types/pagination";
import type { Pipeline, PipelineDetail, PipelineInput, PipelinesListParams, PipelineStage, PipelineStageInput } from "@/types/pipeline";
import { toQueryString } from "@/utils/query-string";

export const pipelineService = {
  create(input: PipelineInput): Promise<PipelineDetail> { return apiClient.post<PipelineDetail>("/pipelines", JSON.stringify(input)); },
  createStage(pipelineId: string, input: PipelineStageInput): Promise<PipelineStage> { return apiClient.post<PipelineStage>(`/pipelines/${pipelineId}/stages`, JSON.stringify(input)); },
  get(pipelineId: string): Promise<PipelineDetail> { return apiClient.get<PipelineDetail>(`/pipelines/${pipelineId}`, { cache: "no-store" }); },
  list(params: PipelinesListParams = {}): Promise<PaginatedResponse<Pipeline>> { return apiClient.get<PaginatedResponse<Pipeline>>(`/pipelines${toQueryString(params)}`, { cache: "no-store" }); },
  remove(pipelineId: string): Promise<void> { return apiClient.delete<void>(`/pipelines/${pipelineId}`); },
  removeStage(pipelineId: string, stageId: string): Promise<void> { return apiClient.delete<void>(`/pipelines/${pipelineId}/stages/${stageId}`); },
  update(pipelineId: string, input: Partial<PipelineInput>): Promise<PipelineDetail> { return apiClient.patch<PipelineDetail>(`/pipelines/${pipelineId}`, JSON.stringify(input)); },
  updateStage(pipelineId: string, stageId: string, input: Partial<PipelineStageInput>): Promise<PipelineStage> { return apiClient.patch<PipelineStage>(`/pipelines/${pipelineId}/stages/${stageId}`, JSON.stringify(input)); },
};
