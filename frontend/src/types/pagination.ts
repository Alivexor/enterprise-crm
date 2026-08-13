export type PageMetadata = {
  page: number;
  page_size: number;
  total: number;
};

export type PaginatedResponse<T> = {
  items: T[];
  meta: PageMetadata;
};

export type PaginationParams = {
  page?: number;
  page_size?: number;
};
