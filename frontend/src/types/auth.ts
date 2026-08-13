export type LoginCredentials = {
  email: string;
  password: string;
  mfa_code?: string;
};

export type UserRole = {
  id: string;
  name: string;
};

export type UserPermission = {
  description: string | null;
  id: string;
  name: string;
};

export type AuthenticatedUser = {
  id: string;
  organization_id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  mfa_enabled: boolean;
  permissions: UserPermission[];
  roles: UserRole[];
  created_at: string;
  updated_at: string;
};

export type BackendTokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
};

export type AuthenticationSession = {
  user: AuthenticatedUser;
};
