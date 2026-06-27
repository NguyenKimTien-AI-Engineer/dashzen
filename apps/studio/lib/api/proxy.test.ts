import { describe, expect, it } from "vitest";

import { rewriteProxySetCookie } from "./proxy";

describe("rewriteProxySetCookie", () => {
  it("rewrites refresh cookie path and strips domain", () => {
    const raw =
      "dashzen_refresh_token=abc; HttpOnly; Path=/v1/auth; SameSite=lax; Secure; Domain=dashzen-api.onrender.com";
    expect(rewriteProxySetCookie(raw)).toBe(
      "dashzen_refresh_token=abc; HttpOnly; Path=/api/v1/auth; SameSite=lax; Secure",
    );
  });

  it("leaves access cookie path unchanged", () => {
    const raw = "dashzen_access_token=abc; HttpOnly; Path=/; SameSite=lax; Secure";
    expect(rewriteProxySetCookie(raw)).toBe(raw);
  });
});
