import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getApiBackendUrl,
  getApiBaseUrl,
  getBrowserApiBaseUrl,
  isProxiedApi,
  resolveApiUrl,
} from "./config";

describe("getApiBaseUrl", () => {
  it("strips trailing slash", () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000/");
    expect(getApiBaseUrl()).toBe("http://localhost:8000");
  });
});

describe("getBrowserApiBaseUrl", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("returns relative base unchanged", () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "/api");
    expect(getBrowserApiBaseUrl()).toBe("/api");
  });

  it("uses /api proxy when configured host differs from window origin", () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://dashzen-api.onrender.com");
    vi.stubGlobal("window", {
      location: { origin: "https://dashzen-mu.vercel.app" },
    } as Window & typeof globalThis);
    expect(getBrowserApiBaseUrl()).toBe("/api");
  });

  it("keeps localhost API for local dev", () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000");
    vi.stubGlobal("window", {
      location: { origin: "http://localhost:3000" },
    } as Window & typeof globalThis);
    expect(getBrowserApiBaseUrl()).toBe("http://localhost:8000");
  });
});

describe("getApiBackendUrl", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("prefers API_BACKEND_URL when public URL is relative", () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "/api");
    vi.stubEnv("API_BACKEND_URL", "https://dashzen-api.onrender.com/");
    expect(getApiBackendUrl()).toBe("https://dashzen-api.onrender.com");
  });

  it("falls back to public http URL", () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000");
    vi.stubEnv("API_BACKEND_URL", "");
    expect(getApiBackendUrl()).toBe("http://localhost:8000");
  });
});

describe("resolveApiUrl", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("joins relative path with /api base", () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "/api");
    vi.stubGlobal("window", undefined);
    expect(resolveApiUrl("/v1/auth/login")).toBe("/api/v1/auth/login");
  });
});

describe("isProxiedApi", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("is true for relative public URL", () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "/api");
    expect(isProxiedApi()).toBe(true);
  });
});
