import type { Message } from "@/modules/task/types/api";

/** Latest user message by created_at (matches backend find_orphan_user_message). */
export function findLatestUserMessage(messages: Message[]): Message | null {
  let latest: Message | null = null;
  for (const message of messages) {
    if (message.role !== "user") continue;
    if (!latest || message.created_at > latest.created_at) {
      latest = message;
    }
  }
  return latest;
}

export function hasAssistantReply(messages: Message[], userId: string): boolean {
  return messages.some((m) => m.role === "assistant" && m.parent_id === userId);
}

/** True when the latest user turn has no assistant reply in the thread. */
export function isThreadAwaitingReply(messages: Message[]): boolean {
  const latestUser = findLatestUserMessage(messages);
  if (!latestUser) return false;
  return !hasAssistantReply(messages, latestUser.id);
}

/** Content to resend when a user message was interrupted with no assistant reply. */
export function findOrphanUserMessage(messages: Message[]): string | null {
  if (!isThreadAwaitingReply(messages)) return null;
  const content = findLatestUserMessage(messages)?.content.trim();
  return content || null;
}
