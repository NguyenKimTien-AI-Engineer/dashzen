"use client";

import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { AppSidebar } from "@/modules/layout/components/AppSidebar";
import { isChatLayoutPath } from "@/modules/layout/lib/routes";
import { SettingsPanel } from "@/modules/settings/components/SettingsPanel";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? "";
  const isChatLayout = isChatLayoutPath(pathname);

  return (
    <>
      <AppSidebar />
      <main
        className={cn(
          "flex min-w-0 flex-1 flex-col bg-background",
          isChatLayout ? "h-full overflow-hidden" : "overflow-auto p-8",
        )}
      >
        {children}
      </main>
      <SettingsPanel />
    </>
  );
}
