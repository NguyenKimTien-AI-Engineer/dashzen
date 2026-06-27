/** Rewrite Set-Cookie from Render so cookies apply to the Studio `/api` proxy path. */
export function rewriteProxySetCookie(cookie: string): string {
  return cookie
    .replace(/;\s*Domain=[^;]*/gi, "")
    .replace(/;\s*Path=\/v1\/auth\b/gi, "; Path=/api/v1/auth");
}
