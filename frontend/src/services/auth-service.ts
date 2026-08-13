import { apiClient } from "@/services/api-client";
import type {
  AuthenticatedUser,
  AuthenticationSession,
  LoginCredentials,
} from "@/types/auth";

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthenticationSession> {
    return apiClient.post<AuthenticationSession>(
      "/auth/login",
      JSON.stringify(credentials),
    );
  },

  async getCurrentUser(): Promise<AuthenticatedUser> {
    return apiClient.get<AuthenticatedUser>("/auth/me", { cache: "no-store" });
  },

  async logout(): Promise<void> {
    await apiClient.post<void>("/auth/logout");
  },
};
