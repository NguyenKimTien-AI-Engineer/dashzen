export type User = {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  email_verified: boolean;
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
