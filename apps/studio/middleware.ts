import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const AUTH_ROUTES = ["/login", "/register", "/verify-email"];
const PROTECTED_PREFIX = "/app";
const ACCESS_COOKIE = "dashzen_access_token";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasAccess = request.cookies.has(ACCESS_COOKIE);

  const isAuthRoute = AUTH_ROUTES.some(
    (r) => pathname === r || pathname.startsWith(`${r}/`),
  );
  const isProtected = pathname.startsWith(PROTECTED_PREFIX);

  if (isAuthRoute && hasAccess) {
    return NextResponse.redirect(new URL("/app", request.url));
  }

  if (isProtected && !hasAccess) {
    const login = new URL("/login", request.url);
    login.searchParams.set("return_to", pathname);
    return NextResponse.redirect(login);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/app", "/app/:path*", "/login", "/register", "/verify-email"],
};
