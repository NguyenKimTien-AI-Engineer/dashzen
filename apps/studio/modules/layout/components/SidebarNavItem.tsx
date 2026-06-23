"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

type SidebarNavItemProps = {
  href: string;
  label: string;
  icon: ReactNode;
  collapsed: boolean;
};

export function SidebarNavItem({
  href,
  label,
  icon,
  collapsed,
}: SidebarNavItemProps) {
  const link = (
    <Link
      href={href}
      className={cn(
        "flex items-center rounded-lg bg-white text-sm font-medium text-foreground/80 transition-colors active:bg-muted active:text-foreground",
        collapsed ? "size-9 justify-center" : "h-9 gap-3 px-3",
      )}
    >
      {icon}
      {!collapsed && <span className="truncate">{label}</span>}
    </Link>
  );

  if (!collapsed) {
    return link;
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>{link}</TooltipTrigger>
      <TooltipContent side="right">{label}</TooltipContent>
    </Tooltip>
  );
}
