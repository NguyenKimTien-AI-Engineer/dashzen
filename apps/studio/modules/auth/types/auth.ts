export type AuthProvider = "password" | "google";

export type User = {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  email_verified: boolean;
  has_password: boolean;
  auth_providers: AuthProvider[];
  created_at: string | null;
};

export type RegisterResponse = {
  user: User;
  requires_verification: boolean;
};

export type AuthUserResponse = {
  user: User;
};

export type OkResponse = {
  ok: boolean;
};
