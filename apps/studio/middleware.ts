import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Studio (Vercel) and API (Render) are different origins. Auth cookies are set on
 * the API host and sent with fetch(credentials: "include") — they are not visible
 * on the Studio host, so cookie checks here would block /app after a successful login.
 *
 * Protected routes rely on client-side AuthGuard (/v1/auth/me on the API).
 */
export function middleware(_request: NextRequest) {
  return NextResponse.next();
}

export const config = {
  matcher: ["/app", "/app/:path*", "/login", "/register", "/verify-email"],
};
