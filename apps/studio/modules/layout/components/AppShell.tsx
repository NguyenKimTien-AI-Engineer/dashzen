"use client";

import { AppSidebar } from "@/modules/layout/components/AppSidebar";
import { SettingsPanel } from "@/modules/settings/components/SettingsPanel";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <AppSidebar />
      <main className="flex-1 overflow-auto p-8">{children}</main>
      <SettingsPanel />
    </>
  );
}
