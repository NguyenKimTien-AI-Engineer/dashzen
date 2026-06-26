"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronsUpDown, LogOut, Settings, User } from "lucide-react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { useSettingsPanelStore } from "@/lib/stores/settingsPanelStore";
import { useLogout } from "@/modules/auth/hooks/useAuth";
import { useMe } from "@/modules/auth/hooks/useMe";
import { UserAvatar } from "@/modules/auth/components/UserAvatar";

type SidebarUserMenuProps = {
  collapsed: boolean;
};

export function SidebarUserMenu({ collapsed }: SidebarUserMenuProps) {
  const router = useRouter();
  const { data: user } = useMe();
  const logoutMutation = useLogout();
  const openPanel = useSettingsPanelStore((state) => state.openPanel);
  const [popoverOpen, setPopoverOpen] = useState(false);

  if (!user) return null;

  const displayLabel = user.display_name?.trim() || user.email.split("@")[0];

  function openSettingsTab(tab: "general" | "account") {
    setPopoverOpen(false);
    openPanel(tab);
  }

  function handleLogout() {
    logoutMutation.mutate(undefined, {
      onSuccess: () => {
        setPopoverOpen(false);
        router.push("/login");
      },
    });
  }

  const popoverWidthClass = collapsed
    ? "w-56"
    : "w-[var(--radix-popover-trigger-width)]";

  const avatar = (
    <UserAvatar
      displayName={user.display_name}
      email={user.email}
      avatarUrl={user.avatar_url}
      size="sm"
    />
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
      <div className="my-1 h-px bg-border" />
      <button
        type="button"
        onClick={handleLogout}
        disabled={logoutMutation.isPending}
        className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm text-destructive hover:bg-muted disabled:opacity-50"
      >
        <LogOut className="size-4 shrink-0" />
        {logoutMutation.isPending ? "Signing out..." : "Log out"}
      </button>
    </>
  );

  if (collapsed) {
    return (
      <div className="flex justify-center p-2">
        <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
          <Tooltip>
            <TooltipTrigger asChild>
              <PopoverTrigger asChild>
                <button
                  type="button"
                  className="flex size-9 items-center justify-center rounded-lg hover:bg-muted"
                  aria-label="Account menu"
                >
                  {avatar}
                </button>
              </PopoverTrigger>
            </TooltipTrigger>
            <TooltipContent side="right">Account</TooltipContent>
          </Tooltip>
          <PopoverContent side="right" align="end" sideOffset={8} className={cn(popoverWidthClass, "p-1")}>
            {menuItems}
          </PopoverContent>
        </Popover>
      </div>
    );
  }

  return (
    <div className="p-2">
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
        <PopoverContent side="top" align="start" sideOffset={4} className={cn(popoverWidthClass, "p-1")}>
          {menuItems}
        </PopoverContent>
      </Popover>
    </div>
  );
}
