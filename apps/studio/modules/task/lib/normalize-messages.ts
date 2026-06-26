import type { Message } from "@/modules/task/types/api";
import type { ActivityLogPayload } from "@/modules/task/types/activity-log";
import { isActivityLogPayload } from "@/modules/task/types/activity-log";
import type { DisplayMessage } from "@/modules/task/types/task-state";

type ToolCallEntry = { id: string; name: string; input?: unknown };

function isToolCallArray(value: unknown): value is ToolCallEntry[] {
  return (
    Array.isArray(value) &&
    value.length > 0 &&
    value.every(
      (item) =>
        typeof item === "object" &&
        item !== null &&
        typeof (item as ToolCallEntry).id === "string" &&
        typeof (item as ToolCallEntry).name === "string",
    )
  );
}

function hasToolCallPayload(content: string): boolean {
  const trimmed = content.trim();
  const legacyMarker = '{"tool_calls"';
  if (trimmed.includes(legacyMarker)) return true;

  const bracketIdx = trimmed.lastIndexOf("[");
  if (bracketIdx !== -1) {
    const candidate = trimmed.slice(bracketIdx);
    try {
      const parsed: unknown = JSON.parse(candidate);
      if (isToolCallArray(parsed)) return true;
    } catch {
      // ignore parse errors
    }
  }

  if (trimmed.startsWith("[")) {
    try {
      const parsed: unknown = JSON.parse(trimmed);
      if (isToolCallArray(parsed)) return true;
    } catch {
      // ignore parse errors
    }
  }
  return false;
}

/** Strip embedded tool-call JSON appended by the backend to assistant messages. */
export function stripAssistantContent(content: string): string {
  let result = content.trim();

  const legacyMarker = '{"tool_calls"';
  const legacyIdx = result.indexOf(legacyMarker);
  if (legacyIdx !== -1) {
    result = result.slice(0, legacyIdx).trim();
  }

  const bracketIdx = result.lastIndexOf("[");
  if (bracketIdx !== -1) {
    const candidate = result.slice(bracketIdx);
    try {
      const parsed: unknown = JSON.parse(candidate);
      if (isToolCallArray(parsed)) {
        result = result.slice(0, bracketIdx).trim();
      }
    } catch {
      // not a tool-call payload
    }
  }

  // Content that is only a tool-call JSON array
  if (result.startsWith("[")) {
    try {
      const parsed: unknown = JSON.parse(result);
      if (isToolCallArray(parsed)) return "";
    } catch {
      // keep as-is
    }
  }

  return result;
}

export function normalizeMessages(apiMessages: Message[]): DisplayMessage[] {
  return apiMessages
    .filter((m) => m.role === "user" || m.role === "assistant")
    .map((m) => {
      const activityLog: ActivityLogPayload | undefined = isActivityLogPayload(m.activity_log)
        ? m.activity_log
        : undefined;
      const hasToolCalls = m.role === "assistant" && hasToolCallPayload(m.content);
      return {
        id: m.id,
        role: m.role as "user" | "assistant",
        content: m.role === "assistant" ? stripAssistantContent(m.content) : m.content,
        status: "sent" as const,
        createdAt: new Date(m.created_at),
        activityLog,
        hasToolCalls,
        userFeedback: m.user_feedback ?? null,
      };
    })
    .filter((m) => m.role === "user" || m.content.length > 0 || m.activityLog || m.hasToolCalls);
}
