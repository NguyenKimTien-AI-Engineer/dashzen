import type { ActivityLogPayload } from "@/modules/task/types/activity-log";
import type { DisplayMessage } from "@/modules/task/types/task-state";

/** Latest activity log attached to any assistant message in a grouped turn. */
export function getAssistantGroupActivityLog(
  messages: DisplayMessage[],
): ActivityLogPayload | undefined {
  let latest: ActivityLogPayload | undefined;
  for (const message of messages) {
    if (message.activityLog) latest = message.activityLog;
  }
  return latest;
}
