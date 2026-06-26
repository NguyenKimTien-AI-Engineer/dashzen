"use client";

import { useMemo } from "react";
import { composeChatMessages } from "@/modules/task/lib/compose-chat-messages";
import { normalizeMessages } from "@/modules/task/lib/normalize-messages";
import type { DisplayMessage } from "@/modules/task/types/task-state";
import { useTaskContext } from "../contexts/task-context";
import { useTaskMessages } from "./useTaskMessages";

/**
 * Persisted history from React Query, plus an optional in-flight user turn
 * from the stream session reducer.
 */
export function useChatDisplayMessages(taskId: string): DisplayMessage[] {
  const { state } = useTaskContext();
  const { data, isSuccess } = useTaskMessages(taskId);

  return useMemo(() => {
    const persisted = isSuccess && data ? normalizeMessages(data) : [];
    return composeChatMessages(persisted, state.streamTurn);
  }, [data, isSuccess, state.streamTurn]);
}
