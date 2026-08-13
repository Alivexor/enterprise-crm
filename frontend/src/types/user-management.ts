import type { UserPermission, UserRole } from "@/types/auth";
import type { PaginationParams } from "@/types/pagination";

export type ManagedUser = {
  created_at: string;
  email: string;
  first_name: string;
  id: string;
  is_active: boolean;
  last_name: string;
  organization_id: string;
  permissions: UserPermission[];
  roles: UserRole[];
  updated_at: string;
};

export type ManagedUserCreate = {
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  role_ids: string[];
};

export type ManagedUserUpdate = {
  email?: string;
  first_name?: string;
  is_active?: boolean;
  last_name?: string;
  role_ids?: string[];
};

export type ProfileUpdate = {
  email?: string;
  first_name?: string;
  last_name?: string;
};

export type PasswordChange = {
  current_password: string;
  new_password: string;
};

export type UsersListParams = PaginationParams & {
  is_active?: boolean;
  search?: string;
};
