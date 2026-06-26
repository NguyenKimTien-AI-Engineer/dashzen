import type { QueryClient } from "@tanstack/react-query";
import type { Message } from "@/modules/task/types/api";
import type { StreamTurn } from "@/modules/task/types/task-state";
import { taskKeys } from "./query-keys";

export type StreamSnapshot = {
  streamTurn: StreamTurn | null;
  streamingText: string;
};

export function patchMessageCacheAfterStream(
  queryClient: QueryClient,
  taskId: string,
  snapshot: StreamSnapshot,
) {
  const { streamTurn, streamingText } = snapshot;
  const assistantContent = streamingText.trim();
  if (!streamTurn && !assistantContent) return;

  queryClient.setQueryData<Message[]>(taskKeys.messages(taskId), (old = []) => {
    const chain = [...old];
    const now = new Date().toISOString();

    if (streamTurn) {
      const userExists = chain.some(
        (m) => m.role === "user" && m.content === streamTurn.userContent,
      );
      if (!userExists) {
        chain.push({
          id: streamTurn.optimisticUserId,
          role: "user",
          content: streamTurn.userContent,
          parent_id: chain.at(-1)?.id ?? null,
          prompt_tokens: null,
          created_at: now,
        });
      }
    }

    if (assistantContent) {
      const assistantExists = chain.some(
        (m) => m.role === "assistant" && m.content === assistantContent,
      );
      if (!assistantExists) {
        chain.push({
          id: `optimistic-assistant-${Date.now()}`,
          role: "assistant",
          content: assistantContent,
          parent_id: chain.at(-1)?.id ?? null,
          prompt_tokens: null,
          created_at: now,
        });
      }
    }

    return chain;
  });
}

export function getLastMessageParentId(
  queryClient: QueryClient,
  taskId: string,
): string | null {
  const messages = queryClient.getQueryData<Message[]>(taskKeys.messages(taskId));
  if (!messages || messages.length === 0) return null;
  return messages.at(-1)?.id ?? null;
}
