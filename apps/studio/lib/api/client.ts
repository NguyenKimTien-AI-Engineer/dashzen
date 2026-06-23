import { ApiError, ApiErrorBody, RateLimitError, SessionExpiredError } from "./errors";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

let refreshPromise: Promise<boolean> | null = null;

async function tryRefreshToken(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const res = await fetch(`${API_URL}/v1/auth/refresh`, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
        });
        return res.ok;
      } catch {
        return false;
      } finally {
        refreshPromise = null;
      }
    })();
  }
  return refreshPromise;
}

/** Silent session refresh — use before redirecting to login. */
export async function refreshSession(): Promise<boolean> {
  return tryRefreshToken();
}

function redirectToLogin() {
  if (typeof window !== "undefined") {
    // preserve current pathname as return_to
    const returnTo = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.href = `/login?return_to=${returnTo}`;
  }
}

export async function fetchWithAuth(
  path: string,
  options: RequestInit = {},
  retried = false,
): Promise<Response> {
  const url = path.startsWith("http") ? path : `${API_URL}${path}`;
  const res = await fetch(url, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (res.status === 401 && !path.startsWith("/v1/auth/") && !retried) {
    const refreshed = await tryRefreshToken();
    if (refreshed) return fetchWithAuth(path, options, true);
    redirectToLogin();
    throw new SessionExpiredError();
  }

  if (res.status === 429) {
    const retryAfter = res.headers.get("Retry-After");
    throw new RateLimitError(retryAfter);
  }

  if (!res.ok) {
    let body: ApiErrorBody;
    try {
      body = await res.json() as ApiErrorBody;
    } catch {
      throw new Error(`HTTP ${res.status}`);
    }
    throw new ApiError(res.status, body.error?.code || "unknown_error", body.error || { code: "unknown_error", message: `HTTP ${res.status}` });
  }

  return res;
}

export async function fetchPublic(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  const url = path.startsWith("http") ? path : `${API_URL}${path}`;
  const res = await fetch(url, {
    ...options,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...options.headers },
  });

  if (res.status === 429) {
    const retryAfter = res.headers.get("Retry-After");
    throw new RateLimitError(retryAfter);
  }

  if (!res.ok) {
    let body: ApiErrorBody;
    try {
      body = await res.json() as ApiErrorBody;
    } catch {
      throw new Error(`HTTP ${res.status}`);
    }
    throw new ApiError(res.status, body.error?.code || "unknown_error", body.error || { code: "unknown_error", message: `HTTP ${res.status}` });
  }

  return res;
}
