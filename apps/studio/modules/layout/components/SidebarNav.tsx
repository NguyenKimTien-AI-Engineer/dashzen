"use client";

import { SidebarNavItem } from "./SidebarNavItem";
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
  return (
    <nav className="flex flex-col gap-1 p-2" aria-label="Main navigation">
      {NAV_ITEMS.map((item) => (
        <SidebarNavItem
          key={item.href}
          href={item.href}
          label={item.label}
          icon={item.icon}
          collapsed={collapsed}
        />
      ))}
    </nav>
  );
}
