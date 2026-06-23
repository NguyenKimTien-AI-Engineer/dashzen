import { create } from "zustand";

export type SettingsTab = "general" | "account" | "privacy";

type SettingsPanelStore = {
  open: boolean;
  tab: SettingsTab;
  openPanel: (tab?: SettingsTab) => void;
  closePanel: () => void;
  setTab: (tab: SettingsTab) => void;
};

export const useSettingsPanelStore = create<SettingsPanelStore>((set) => ({
  open: false,
  tab: "general",
  openPanel: (tab = "general") => set({ open: true, tab }),
  closePanel: () => set({ open: false }),
  setTab: (tab) => set({ tab }),
}));
