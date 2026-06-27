import { cookies } from "next/headers";

import { getApiBackendUrl } from "./config";

export async function serverFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((cookie) => `${cookie.name}=${cookie.value}`)
    .join("; ");

  const normalized = path.startsWith("/") ? path : `/${path}`;
  const url = path.startsWith("http") ? path : `${getApiBackendUrl()}${normalized}`;

  return fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(cookieHeader ? { Cookie: cookieHeader } : {}),
      ...init.headers,
    },
    cache: "no-store",
  });
}

export async function serverGetJson<T>(path: string): Promise<T | null> {
  try {
    const res = await serverFetch(path);
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}
