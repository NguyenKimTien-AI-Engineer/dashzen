import type { ReactNode } from "react";

import { cn } from "../../../lib/utils";

type SettingsSectionProps = {
  title: string;
  description: string;
  action: ReactNode;
  danger?: boolean;
};

export function SettingsSection({
  title,
  description,
  action,
  danger = false,
}: SettingsSectionProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-4 rounded-lg border bg-card p-6 shadow-sm sm:flex-row sm:items-center sm:justify-between",
        danger && "border-destructive/30",
      )}
    >
      <div className="space-y-1">
        <h2 className={cn("text-lg font-semibold", danger && "text-destructive")}>{title}</h2>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <div className="shrink-0">{action}</div>
    </div>
  );
}
