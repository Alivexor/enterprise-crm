"use client";

import { useEffect, useState } from "react";

import { ApiError } from "@/services/api-client";
import { leadService } from "@/services/lead-service";
import type { Lead } from "@/types/lead";

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "Unable to load lead options.";
}

export function useLeadOptions() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isActive = true;

    async function loadLeads() {
      try {
        const response = await leadService.list({
          page: 1,
          page_size: 100,
          sort_by: "title",
        });
        if (isActive) {
          setLeads(response.items);
          setError(null);
        }
      } catch (caughtError) {
        if (isActive) {
          setError(getErrorMessage(caughtError));
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void loadLeads();
    return () => {
      isActive = false;
    };
  }, []);

  return { leads, error, isLoading };
}
