"use client";

import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { SidebarNavItem } from "./SidebarNavItem";
import { SidebarRecents } from "./SidebarRecents";
import {
  ArtifactsIcon,
  ChatsIcon,
  NewChatIcon,
  ProjectsIcon,
} from "./sidebar-icons";

const NAV_ITEMS = [
  { href: "/app", label: "New chat", icon: <NewChatIcon /> },
  { href: "/app/chats", label: "Chats", icon: <ChatsIcon /> },
  { href: "/app/projects", label: "Projects", icon: <ProjectsIcon /> },
  { href: "/app/artifacts", label: "Artifacts", icon: <ArtifactsIcon /> },
] as const;

type SidebarNavProps = {
  collapsed: boolean;
};

export function SidebarNav({ collapsed }: SidebarNavProps) {
  const pathname = usePathname() ?? "";
  const isHome = pathname === "/app";

  return (
    <>
      <nav
        className={cn("flex flex-col gap-1 p-2", collapsed && "items-center")}
        aria-label="Main navigation"
      >
        {NAV_ITEMS.map((item) => (
          <SidebarNavItem
            key={item.href}
            href={item.href}
            label={item.label}
            icon={item.icon}
            collapsed={collapsed}
            active={
              item.href === "/app"
                ? isHome
                : item.href === "/app/chats"
                  ? pathname === "/app/chats"
                  : item.href === "/app/projects"
                    ? pathname.startsWith("/app/projects")
                    : item.href === "/app/artifacts"
                      ? pathname.startsWith("/app/artifacts")
                      : undefined
            }
          />
        ))}
      </nav>
      <SidebarRecents collapsed={collapsed} />
    </>
  );
}
