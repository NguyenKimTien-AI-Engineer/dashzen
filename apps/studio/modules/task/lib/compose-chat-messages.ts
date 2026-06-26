import type { DisplayMessage, StreamTurn } from "@/modules/task/types/task-state";

/**
 * Overlay the in-flight user turn on top of persisted API messages.
 * Persisted history always comes from React Query; this only fills the gap
 * while the current user message has not been written to the cache yet.
 */
export function composeChatMessages(
  persisted: DisplayMessage[],
  streamTurn: StreamTurn | null,
): DisplayMessage[] {
  if (!streamTurn) return persisted;

  const userAlreadyVisible = persisted.some(
    (m) => m.role === "user" && m.content === streamTurn.userContent,
  );
  if (userAlreadyVisible) return persisted;

  return [
    ...persisted,
    {
      id: streamTurn.optimisticUserId,
      role: "user",
      content: streamTurn.userContent,
      status: "sent",
      createdAt: new Date(streamTurn.startedAt),
    },
  ];
}
