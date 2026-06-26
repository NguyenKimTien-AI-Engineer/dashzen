export const CHAT_LAYOUT_PATHS = [
  "/app",
  "/app/chats",
  "/app/projects",
  "/app/artifacts",
  "/app/task",
] as const;

export function isChatLayoutPath(pathname: string): boolean {
  return (
    pathname === "/app" ||
    pathname === "/app/chats" ||
    pathname.startsWith("/app/projects") ||
    pathname.startsWith("/app/artifacts") ||
    pathname.startsWith("/app/task/")
  );
}
