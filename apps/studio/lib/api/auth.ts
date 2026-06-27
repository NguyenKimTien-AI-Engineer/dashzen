import { fetchPublic, fetchWithAuth } from "./client";
import { resolveApiUrl } from "./config";
import type { AuthUserResponse, OkResponse, RegisterResponse, User } from "@/modules/auth/types/auth";

export const googleOAuthEnabled =
  process.env.NEXT_PUBLIC_GOOGLE_OAUTH_ENABLED === "true";

export const githubOAuthEnabled =
  process.env.NEXT_PUBLIC_GITHUB_OAUTH_ENABLED === "true";

export function startGoogleLogin(returnTo = "/app"): void {
  const params = new URLSearchParams({ return_to: returnTo });
  window.location.assign(resolveApiUrl(`/v1/auth/google?${params}`));
}

export function startGitHubLogin(returnTo = "/app"): void {
  const params = new URLSearchParams({ return_to: returnTo });
  window.location.assign(resolveApiUrl(`/v1/auth/github?${params}`));
}

export async function login(email: string, password: string): Promise<AuthUserResponse> {
  const res = await fetchPublic("/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  return res.json();
}

export async function register(
  email: string,
  password: string,
  displayName?: string,
): Promise<RegisterResponse> {
  const res = await fetchPublic("/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({
      email,
      password,
      display_name: displayName ?? null,
    }),
  });
  return res.json();
}

export async function verifyEmail(email: string, code: string): Promise<OkResponse> {
  const res = await fetchPublic("/v1/auth/verify-email", {
    method: "POST",
    body: JSON.stringify({ email, code }),
  });
  return res.json();
}

export async function resendVerification(email: string): Promise<OkResponse> {
  const res = await fetchPublic("/v1/auth/resend-verification", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
  return res.json();
}

export async function logoutApi(): Promise<OkResponse> {
  const res = await fetchPublic("/v1/auth/logout", {
    method: "POST",
  });
  return res.json();
}

export async function getMe(): Promise<User> {
  const res = await fetchWithAuth("/v1/auth/me", {
    method: "GET",
  });
  return res.json();
}

export async function updateProfile(displayName: string): Promise<User> {
  const res = await fetchWithAuth("/v1/auth/me", {
    method: "PATCH",
    body: JSON.stringify({ display_name: displayName }),
  });
  return res.json();
}

export async function uploadAvatar(file: File): Promise<User> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetchWithAuth("/v1/auth/me/avatar", {
    method: "POST",
    body: form,
  });
  return res.json();
}

export async function deleteAvatar(): Promise<User> {
  const res = await fetchWithAuth("/v1/auth/me/avatar", {
    method: "DELETE",
  });
  return res.json();
}

export async function changePassword(
  currentPassword: string,
  newPassword: string,
): Promise<OkResponse> {
  const res = await fetchWithAuth("/v1/auth/change-password", {
    method: "POST",
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });
  return res.json();
}

export async function deleteAccount(
  confirmation: "DELETE",
  password?: string,
): Promise<OkResponse> {
  const res = await fetchWithAuth("/v1/auth/me", {
    method: "DELETE",
    body: JSON.stringify({
      password: password ?? null,
      confirmation,
    }),
  });
  return res.json();
}
