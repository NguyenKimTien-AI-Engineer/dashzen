"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

type SidebarNavItemProps = {
  href: string;
  label: string;
  icon: ReactNode;
  collapsed: boolean;
  active?: boolean;
  onClick?: () => void;
};

export function SidebarNavItem({
  href,
  label,
  icon,
  collapsed,
  active,
  onClick,
}: SidebarNavItemProps) {
  const pathname = usePathname();
  const isActive = active ?? pathname === href;

  const className = cn(
    "flex items-center rounded-lg text-sm font-medium transition-colors",
    isActive
      ? "bg-muted text-foreground"
      : "text-foreground/80 hover:bg-muted/60 hover:text-foreground",
    collapsed ? "size-9 justify-center" : "h-9 gap-3 px-3",
  );

  const content = (
    <>
      {icon}
      {!collapsed && <span className="truncate">{label}</span>}
    </>
  );

  const link =
    onClick ? (
      <button type="button" onClick={onClick} className={cn(className, "w-full")}>
        {content}
      </button>
    ) : (
      <Link href={href} className={className}>
        {content}
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
