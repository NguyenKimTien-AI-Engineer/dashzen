"use client";

import Link from "next/link";
import { ChevronsUpDown, Search, PanelLeftClose } from "lucide-react";
import { toast } from "sonner";

import { DashZenIcon } from "@/components/brand/dashzen-icon";
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
      <div className="flex h-12 items-center justify-center border-b px-2">
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              onClick={toggle}
              className="rounded-lg p-1.5 transition-opacity hover:opacity-80"
              aria-label="Expand sidebar"
            >
              <DashZenIcon size={28} />
            </button>
          </TooltipTrigger>
          <TooltipContent side="right">Expand sidebar</TooltipContent>
        </Tooltip>
      </div>
    );
  }

  return (
    <div className="flex h-12 items-center justify-between gap-2 border-b px-3">
      <DashZenLogo showStudio href="/app" iconSize={24} className="min-w-0" />
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
