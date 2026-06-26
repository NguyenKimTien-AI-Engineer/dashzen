export type SettingsTab = "general" | "account" | "privacy";

export type SettingsPanelState = {
  open: boolean;
  tab: SettingsTab;
};
