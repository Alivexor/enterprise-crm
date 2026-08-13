export const importExportResources = ["companies", "contacts"] as const;

export type ImportExportResource = (typeof importExportResources)[number];

export type ImportRowError = {
  field: string | null;
  message: string;
  row_number: number;
};

export type ImportResponse = {
  created_count: number;
  resource: ImportExportResource;
  rows_processed: number;
};
