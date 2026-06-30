import type { QueryClient } from "@tanstack/react-query";
import type { Message } from "@/modules/task/types/api";
import type { ActivityLogPayload } from "@/modules/task/types/activity-log";
import { isActivityLogPayload } from "@/modules/task/types/activity-log";
import { activityLogHasContent } from "@/modules/task/lib/build-live-activity-log";
import type { StreamTurn, TurnUsage } from "@/modules/task/types/task-state";
import { taskKeys } from "./query-keys";

export type StreamSnapshot = {
  streamTurn: StreamTurn | null;
  streamingText: string;
  activityLog?: ActivityLogPayload | null;
  turnUsage?: TurnUsage | null;
};

function attachUsageToActivityLog(
  log: ActivityLogPayload | null | undefined,
  turnUsage: TurnUsage | null | undefined,
): ActivityLogPayload | undefined {
  if (!log || !activityLogHasContent(log)) return undefined;
  if (!turnUsage) return log;
  return {
    ...log,
    usage: {
      input_tokens: turnUsage.inputTokens,
      output_tokens: turnUsage.outputTokens,
    },
  };
}

function activityLogStepCount(log: ActivityLogPayload | null | undefined): number {
  if (!log) return 0;
  return log.sections.reduce((count, section) => count + section.steps.length, 0);
}

export function mergeRicherActivityLogAfterRefetch(
  queryClient: QueryClient,
  taskId: string,
  snapshot: StreamSnapshot,
) {
  const liveLog = attachUsageToActivityLog(snapshot.activityLog, snapshot.turnUsage);
  if (!liveLog) return;

  const liveSteps = activityLogStepCount(liveLog);
  if (liveSteps === 0) return;

  queryClient.setQueryData<Message[]>(taskKeys.messages(taskId), (old) => {
    if (!old?.length) return old;

    let lastAssistantIndex = -1;
    for (let i = old.length - 1; i >= 0; i -= 1) {
      if (old[i]?.role === "assistant") {
        lastAssistantIndex = i;
        break;
      }
    }
    if (lastAssistantIndex === -1) return old;

    const assistant = old[lastAssistantIndex];
    const serverLog = isActivityLogPayload(assistant.activity_log)
      ? assistant.activity_log
      : null;
    if (activityLogStepCount(serverLog) >= liveSteps) return old;

    const next = [...old];
    next[lastAssistantIndex] = {
      ...assistant,
      activity_log: {
        ...liveLog,
        usage: serverLog?.usage ?? liveLog.usage,
      },
    };
    return next;
  });
}

export function patchMessageCacheAfterStream(
  queryClient: QueryClient,
  taskId: string,
  snapshot: StreamSnapshot,
) {
  const { streamTurn, streamingText, activityLog, turnUsage } = snapshot;
  const assistantContent = streamingText.trim();
  if (!streamTurn && !assistantContent) return;

  const resolvedActivityLog = attachUsageToActivityLog(activityLog, turnUsage);

  queryClient.setQueryData<Message[]>(taskKeys.messages(taskId), (old = []) => {
    const chain = [...old];
    const now = new Date().toISOString();

    if (streamTurn) {
      const userExists = chain.some((m) => m.id === streamTurn.optimisticUserId);
      const last = chain.at(-1);
      const serverAlreadyHasUser =
        last?.role === "user" &&
        last.content.trim() === streamTurn.userContent.trim();
      if (!userExists && !serverAlreadyHasUser) {
        chain.push({
          id: streamTurn.optimisticUserId,
          role: "user",
          content: streamTurn.userContent,
          parent_id: resolveParentIdForNewUserMessage(chain),
          prompt_tokens: null,
          created_at: now,
        });
      }
    }

    if (assistantContent && streamTurn) {
      const assistantExists = chain.some((m) => m.id === streamTurn.optimisticAssistantId);
      if (!assistantExists) {
        chain.push({
          id: streamTurn.optimisticAssistantId,
          role: "assistant",
          content: assistantContent,
          parent_id: chain.at(-1)?.id ?? null,
          prompt_tokens: null,
          created_at: now,
          activity_log: resolvedActivityLog,
        });
      }
    }

    return chain;
  });
}

export function resolveParentIdForNewUserMessage(messages: Message[]): string | null {
  if (messages.length === 0) return null;

  const byId = new Map(messages.map((m) => [m.id, m]));
  let current = messages.at(-1)!;

  // Pending user turns (no assistant reply yet) must not become the parent of a new message.
  while (current.role === "user") {
    if (!current.parent_id) return null;
    const parent = byId.get(current.parent_id);
    if (!parent) return current.parent_id;
    current = parent;
  }

  return current.id;
}

export function getLastMessageParentId(
  queryClient: QueryClient,
  taskId: string,
): string | null {
  const messages = queryClient.getQueryData<Message[]>(taskKeys.messages(taskId));
  if (!messages || messages.length === 0) return null;
  return resolveParentIdForNewUserMessage(messages);
}
