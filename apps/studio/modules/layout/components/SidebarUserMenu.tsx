"use client";

import { useState } from "react";
import { ChevronsUpDown, Settings, User } from "lucide-react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { useSettingsPanelStore } from "@/lib/stores/settingsPanelStore";
import { useMe } from "@/modules/auth/hooks/useMe";

type SidebarUserMenuProps = {
  collapsed: boolean;
};

function getUserInitial(displayName: string | null | undefined, email: string): string {
  const source = displayName?.trim() || email;
  return source.charAt(0).toUpperCase() || "?";
}

export function SidebarUserMenu({ collapsed }: SidebarUserMenuProps) {
  const { data: user } = useMe();
  const openPanel = useSettingsPanelStore((state) => state.openPanel);
  const [popoverOpen, setPopoverOpen] = useState(false);

  if (!user) return null;

  const initial = getUserInitial(user.display_name, user.email);
  const displayLabel = user.display_name?.trim() || user.email.split("@")[0];

  function openSettingsTab(tab: "general" | "account") {
    setPopoverOpen(false);
    openPanel(tab);
  }

  const avatar = (
    <span
      className="flex size-8 shrink-0 items-center justify-center rounded-full bg-foreground text-sm font-semibold text-background"
      aria-hidden
    >
      {initial}
    </span>
  );

  const menuItems = (
    <>
      <p className="truncate px-2 py-1.5 text-xs text-muted-foreground">{user.email}</p>
      <div className="my-1 h-px bg-border" />
      <button
        type="button"
        onClick={() => openSettingsTab("general")}
        className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm hover:bg-muted"
      >
        <User className="size-4 shrink-0 text-muted-foreground" />
        Profile
      </button>
      <button
        type="button"
        onClick={() => openSettingsTab("account")}
        className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm hover:bg-muted"
      >
        <Settings className="size-4 shrink-0 text-muted-foreground" />
        Settings
      </button>
    </>
  );

  if (collapsed) {
    return (
      <div className="border-t p-2">
        <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
          <Tooltip>
            <TooltipTrigger asChild>
              <PopoverTrigger asChild>
                <button
                  type="button"
                  className="flex size-9 w-full items-center justify-center rounded-lg hover:bg-muted"
                  aria-label="Account menu"
                >
                  {avatar}
                </button>
              </PopoverTrigger>
            </TooltipTrigger>
            <TooltipContent side="right">Account</TooltipContent>
          </Tooltip>
          <PopoverContent side="right" align="end" className="w-56 p-1">
            {menuItems}
          </PopoverContent>
        </Popover>
      </div>
    );
  }

  return (
    <div className="border-t p-2">
      <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
        <PopoverTrigger asChild>
          <button
            type="button"
            className={cn(
              "flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left transition-colors hover:bg-muted",
            )}
          >
            {avatar}
            <span className="min-w-0 flex-1 truncate text-sm font-medium">{displayLabel}</span>
            <ChevronsUpDown className="size-4 shrink-0 text-muted-foreground" />
          </button>
        </PopoverTrigger>
        <PopoverContent side="top" align="start" className="w-56 p-1">
          {menuItems}
        </PopoverContent>
      </Popover>
    </div>
  );
}
