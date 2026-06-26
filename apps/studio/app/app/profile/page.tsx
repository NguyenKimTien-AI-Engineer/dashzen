"use client";

import { useEffect } from "react";
import { useSettingsPanelStore } from "@/lib/stores/settingsPanelStore";

export default function ProfilePage() {
  const openPanel = useSettingsPanelStore((state) => state.openPanel);

  useEffect(() => {
    openPanel("general");
  }, [openPanel]);

  return null;
}
