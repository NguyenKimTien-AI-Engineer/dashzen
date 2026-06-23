"use client";

import { useEffect, useState } from "react";

import { cn } from "@/lib/utils";
import { useSidebarStore } from "@/lib/stores/sidebarStore";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SidebarHeader } from "./SidebarHeader";
import { SidebarNav } from "./SidebarNav";
import { SidebarUserMenu } from "./SidebarUserMenu";

export function AppSidebar() {
  const collapsed = useSidebarStore((state) => state.collapsed);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const isCollapsed = mounted ? collapsed : false;

  return (
    <TooltipProvider>
      <aside
        className={cn(
          "hidden h-full shrink-0 flex-col border-r bg-muted/20 transition-[width] duration-200 ease-in-out sm:flex",
          isCollapsed ? "w-16" : "w-[calc(16rem+1cm)]",
        )}
        aria-label="Sidebar"
      >
        <SidebarHeader collapsed={isCollapsed} />
        <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
          <SidebarNav collapsed={isCollapsed} />
        </div>
        <SidebarUserMenu collapsed={isCollapsed} />
      </aside>
    </TooltipProvider>
  );
}
