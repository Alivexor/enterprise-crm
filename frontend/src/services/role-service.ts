import { apiClient } from "@/services/api-client";
import type { UserPermission } from "@/types/auth";
import type { Role, RoleInput } from "@/types/role";

export const roleService = {
  create(input: RoleInput): Promise<Role> { return apiClient.post<Role>("/roles", JSON.stringify(input)); },
  list(): Promise<Role[]> { return apiClient.get<Role[]>("/roles", { cache: "no-store" }); },
  listPermissions(): Promise<UserPermission[]> { return apiClient.get<UserPermission[]>("/roles/permissions", { cache: "no-store" }); },
  remove(roleId: string): Promise<void> { return apiClient.delete<void>(`/roles/${roleId}`); },
  update(roleId: string, input: Partial<RoleInput>): Promise<Role> { return apiClient.patch<Role>(`/roles/${roleId}`, JSON.stringify(input)); },
};
