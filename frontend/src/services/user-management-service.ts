import { apiClient } from "@/services/api-client";
import type { PaginatedResponse } from "@/types/pagination";
import type { ManagedUser, ManagedUserCreate, ManagedUserUpdate, PasswordChange, ProfileUpdate, UsersListParams } from "@/types/user-management";
import { toQueryString } from "@/utils/query-string";

export const userManagementService = {
  changePassword(input: PasswordChange): Promise<void> { return apiClient.post<void>("/profile/password", JSON.stringify(input)); },
  create(input: ManagedUserCreate): Promise<ManagedUser> { return apiClient.post<ManagedUser>("/users", JSON.stringify(input)); },
  getProfile(): Promise<ManagedUser> { return apiClient.get<ManagedUser>("/profile", { cache: "no-store" }); },
  list(params: UsersListParams = {}): Promise<PaginatedResponse<ManagedUser>> { return apiClient.get<PaginatedResponse<ManagedUser>>(`/users${toQueryString(params)}`, { cache: "no-store" }); },
  update(userId: string, input: ManagedUserUpdate): Promise<ManagedUser> { return apiClient.patch<ManagedUser>(`/users/${userId}`, JSON.stringify(input)); },
  updateProfile(input: ProfileUpdate): Promise<ManagedUser> { return apiClient.patch<ManagedUser>("/profile", JSON.stringify(input)); },
};
