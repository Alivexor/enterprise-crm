import type { UserPermission } from "@/types/auth";

export type Role = {
  id: string;
  name: string;
  organization_id: string;
  permissions: UserPermission[];
};

export type RoleInput = {
  name: string;
  permission_ids: string[];
};
