import { apiClient } from "@/services/api-client";
import type { Organization, OrganizationInput } from "@/types/organization";

export const organizationService = {
  get(): Promise<Organization> { return apiClient.get<Organization>("/organization", { cache: "no-store" }); },
  update(input: OrganizationInput): Promise<Organization> { return apiClient.patch<Organization>("/organization", JSON.stringify(input)); },
};
