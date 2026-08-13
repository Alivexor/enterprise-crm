import { apiClient } from "@/services/api-client";
import type { ImportExportResource, ImportResponse } from "@/types/import-export";

export const importExportService = {
  exportPath(resource: ImportExportResource): string {
    return `/api/import-export/${resource}`;
  },

  importCsv(resource: ImportExportResource, file: File): Promise<ImportResponse> {
    const formData = new FormData();
    formData.set("file", file);
    return apiClient.post<ImportResponse>(`/import-export/${resource}`, formData);
  },
};
