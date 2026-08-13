"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError } from "@/services/api-client";
import type { PageMetadata, PaginatedResponse } from "@/types/pagination";

const emptyPageMetadata: PageMetadata = {
  page: 1,
  page_size: 25,
  total: 0,
};

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to load this data.";
}

export function usePaginatedResource<T>(
  load: () => Promise<PaginatedResponse<T>>,
) {
  const [items, setItems] = useState<T[]>([]);
  const [meta, setMeta] = useState<PageMetadata>(emptyPageMetadata);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [reloadNonce, setReloadNonce] = useState(0);

  const reload = useCallback(() => {
    setReloadNonce((value) => value + 1);
  }, []);

  useEffect(() => {
    let isActive = true;

    async function loadResource() {
      setIsLoading(true);
      try {
        const response = await load();
        if (isActive) {
          setItems(response.items);
          setMeta(response.meta);
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

    void loadResource();
    return () => {
      isActive = false;
    };
  }, [load, reloadNonce]);

  return { error, isLoading, items, meta, reload };
}
