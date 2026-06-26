import type { DisplayMessage } from "@/modules/task/types/task-state";

/** Last user message in the thread with no assistant reply yet. */
export function findOrphanUserMessage(messages: DisplayMessage[]): string | null {
  if (messages.length === 0) return null;
  const last = messages[messages.length - 1];
  if (last.role !== "user") return null;
  return last.content.trim() || null;
}
