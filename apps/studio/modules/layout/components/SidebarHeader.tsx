"use client";

import { Search, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { toast } from "sonner";

import { DashZenLogo } from "@/components/brand/dashzen-logo";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useSidebarStore } from "@/lib/stores/sidebarStore";

type SidebarHeaderProps = {
  collapsed: boolean;
};

export function SidebarHeader({ collapsed }: SidebarHeaderProps) {
  const toggle = useSidebarStore((state) => state.toggle);

  function handleSearch() {
    toast.info("Search is coming soon.");
  }

  if (collapsed) {
    return (
      <div className="flex justify-center p-2">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon-lg"
              className="rounded-lg"
              onClick={toggle}
              aria-label="Expand sidebar"
            >
              <PanelLeftOpen className="size-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">Expand sidebar</TooltipContent>
        </Tooltip>
      </div>
    );
  }

  return (
    <div className="flex h-12 items-center justify-between gap-2 px-2">
      <DashZenLogo showStudio showIcon={false} href="/app" className="min-w-0 px-3" />
      <div className="flex shrink-0 items-center">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={handleSearch}
              aria-label="Search"
            >
              <Search className="size-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Search</TooltipContent>
        </Tooltip>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={toggle}
              aria-label="Collapse sidebar"
            >
              <PanelLeftClose className="size-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Collapse sidebar</TooltipContent>
        </Tooltip>
      </div>
    </div>
  );
}
