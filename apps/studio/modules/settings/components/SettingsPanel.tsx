"use client";

import { useMemo, useState } from "react";
import { Search, Shield, SlidersHorizontal, User } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import {
  type SettingsTab,
  useSettingsPanelStore,
} from "@/lib/stores/settingsPanelStore";
import { AccountSettingsPanel } from "./AccountSettingsPanel";
import { GeneralSettingsPanel } from "./GeneralSettingsPanel";
import { PrivacySettingsPanel } from "./PrivacySettingsPanel";

const NAV_ITEMS: { id: SettingsTab; label: string; icon: LucideIcon; group: string }[] = [
  { id: "general", label: "General", icon: SlidersHorizontal, group: "Settings" },
  { id: "account", label: "Account", icon: User, group: "Settings" },
  { id: "privacy", label: "Privacy", icon: Shield, group: "Settings" },
];

export function SettingsPanel() {
  const open = useSettingsPanelStore((state) => state.open);
  const tab = useSettingsPanelStore((state) => state.tab);
  const closePanel = useSettingsPanelStore((state) => state.closePanel);
  const setTab = useSettingsPanelStore((state) => state.setTab);
  const [query, setQuery] = useState("");

  const filteredItems = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return NAV_ITEMS;
    return NAV_ITEMS.filter((item) => item.label.toLowerCase().includes(q));
  }, [query]);

  function handleOpenChange(next: boolean) {
    if (!next) {
      closePanel();
      setQuery("");
    }
  }

  const groups = useMemo(() => {
    const map = new Map<string, typeof NAV_ITEMS>();
    for (const item of filteredItems) {
      const list = map.get(item.group) ?? [];
      list.push(item);
      map.set(item.group, list);
    }
    return map;
  }, [filteredItems]);

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="flex h-[min(680px,85vh)] max-h-[85vh] w-[min(920px,92vw)] max-w-[92vw] flex-col gap-0 overflow-hidden p-0 sm:max-w-[920px]">
        <DialogTitle className="sr-only">Settings</DialogTitle>
        <div className="flex min-h-0 flex-1">
          <aside className="flex w-56 shrink-0 flex-col border-r bg-muted/20">
            <div className="border-b p-3">
              <div className="relative">
                <Search className="absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search"
                  className="h-8 pl-8"
                />
              </div>
            </div>
            <nav className="flex-1 overflow-y-auto p-2" aria-label="Settings sections">
              {filteredItems.length === 0 ? (
                <p className="px-2 py-4 text-center text-xs text-muted-foreground">No results</p>
              ) : (
                Array.from(groups.entries()).map(([group, items]) => (
                  <div key={group} className="mb-3">
                    <p className="px-2 py-1.5 text-xs font-medium text-muted-foreground">{group}</p>
                    <ul className="space-y-0.5">
                      {items.map((item) => {
                        const Icon = item.icon;
                        const isActive = tab === item.id;
                        return (
                          <li key={item.id}>
                            <button
                              type="button"
                              onClick={() => setTab(item.id)}
                              className={cn(
                                "flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm transition-colors",
                                isActive
                                  ? "bg-muted font-medium text-foreground"
                                  : "text-foreground/80 hover:bg-muted/60 hover:text-foreground",
                              )}
                            >
                              <Icon className="size-4 shrink-0" />
                              {item.label}
                            </button>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                ))
              )}
            </nav>
          </aside>

          <div className="min-w-0 flex-1 overflow-y-auto p-6">
            {tab === "general" && <GeneralSettingsPanel />}
            {tab === "account" && <AccountSettingsPanel />}
            {tab === "privacy" && <PrivacySettingsPanel />}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
