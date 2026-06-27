const API_PROXY_PREFIX = "/api";

/** Configured API base from NEXT_PUBLIC_API_URL (no trailing slash). */
export function getApiBaseUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_URL ?? "";
  if (!url) {
    throw new Error("NEXT_PUBLIC_API_URL is not set");
  }
  return url.replace(/\/$/, "");
}

/**
 * Browser API base. Production split deploy uses same-origin `/api` so auth cookies
 * are first-party. Local dev keeps direct http://localhost:8000 when origins differ.
 */
export function getBrowserApiBaseUrl(): string {
  const configured = getApiBaseUrl();
  if (configured.startsWith("/")) {
    return configured;
  }

  if (typeof window === "undefined") {
    return configured;
  }

  try {
    const apiUrl = new URL(configured);
    if (apiUrl.origin === window.location.origin) {
      return configured;
    }
    if (apiUrl.hostname === "localhost" || apiUrl.hostname === "127.0.0.1") {
      return configured;
    }
    return API_PROXY_PREFIX;
  } catch {
    return configured;
  }
}

/** True when Studio calls the API through the Next.js `/api` proxy. */
export function isProxiedApi(): boolean {
  const base = getApiBaseUrl();
  if (base.startsWith("/")) {
    return true;
  }
  if (typeof window !== "undefined") {
    return getBrowserApiBaseUrl().startsWith("/");
  }
  return Boolean(process.env.API_BACKEND_URL?.trim());
}

/**
 * Direct upstream API URL for server-side fetches and the proxy handler.
 * Set API_BACKEND_URL on Vercel when NEXT_PUBLIC_API_URL=/api.
 */
export function getApiBackendUrl(): string {
  const backend = process.env.API_BACKEND_URL?.trim();
  if (backend) {
    return backend.replace(/\/$/, "");
  }
  const publicUrl = getApiBaseUrl();
  if (publicUrl.startsWith("http")) {
    return publicUrl;
  }
  throw new Error(
    "API_BACKEND_URL must be set when NEXT_PUBLIC_API_URL is a relative path (e.g. /api)",
  );
}

/** Join API base with a path segment (e.g. /v1/auth/login). */
export function resolveApiUrl(path: string): string {
  if (path.startsWith("http")) {
    return path;
  }
  const base =
    typeof window !== "undefined" ? getBrowserApiBaseUrl() : getApiBaseUrl();
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${base}${normalized}`;
}
