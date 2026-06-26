"use client";

import { useEffect } from "react";
import { useSettingsPanelStore } from "@/lib/stores/settingsPanelStore";

export default function SettingsPage() {
  const openPanel = useSettingsPanelStore((state) => state.openPanel);

  useEffect(() => {
    openPanel("account");
  }, [openPanel]);

  return null;
}
