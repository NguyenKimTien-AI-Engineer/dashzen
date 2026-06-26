export type ActivityStepPayload = {
  id: string;
  kind: "think" | "tool";
  label: string;
  status: string;
  detail: string;
};

export type ActivitySectionPayload = {
  id: string;
  title: string;
  status: "running" | "done" | "error";
  steps: ActivityStepPayload[];
};

export type ActivityLogPayload = {
  type: "activity_log";
  version: number;
  header_title: string;
  sections: ActivitySectionPayload[];
};

export function isActivityLogPayload(value: unknown): value is ActivityLogPayload {
  if (!value || typeof value !== "object") return false;
  const v = value as ActivityLogPayload;
  return v.type === "activity_log" && Array.isArray(v.sections);
}
