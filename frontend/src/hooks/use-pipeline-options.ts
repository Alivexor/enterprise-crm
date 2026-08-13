"use client";

import { useEffect, useState } from "react";

import { ApiError } from "@/services/api-client";
import { pipelineService } from "@/services/pipeline-service";
import type { Pipeline } from "@/types/pipeline";

function getErrorMessage(error: unknown): string { return error instanceof ApiError ? error.message : "Unable to load pipelines."; }

export function usePipelineOptions() {
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  useEffect(() => {
    let isActive = true;
    async function loadPipelines() {
      try { const response = await pipelineService.list({ page: 1, page_size: 100, sort_by: "name" }); if (isActive) { setPipelines(response.items); setError(null); } }
      catch (caughtError) { if (isActive) setError(getErrorMessage(caughtError)); }
      finally { if (isActive) setIsLoading(false); }
    }
    void loadPipelines(); return () => { isActive = false; };
  }, []);
  return { error, isLoading, pipelines };
}
