"use client";

import { useEffect, useState } from "react";

import { ApiError } from "@/services/api-client";
import { companyService } from "@/services/company-service";
import type { Company } from "@/types/company";

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to load company options.";
}

export function useCompanyOptions() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isActive = true;

    async function loadCompanies() {
      try {
        const nextCompanies = await companyService.list({ page: 1, page_size: 100, sort_by: "name" });
        if (isActive) {
          setCompanies(nextCompanies.items);
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

    void loadCompanies();
    return () => {
      isActive = false;
    };
  }, []);

  return { companies, error, isLoading };
}
