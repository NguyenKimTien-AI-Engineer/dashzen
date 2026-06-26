"use client";

import { useEffect, useLayoutEffect, useRef } from "react";
import { toast } from "sonner";
import { getRunStatus } from "@/lib/api/tasks";
import { findOrphanUserMessage } from "@/modules/task/lib/detect-orphan-message";
import { normalizeMessages } from "@/modules/task/lib/normalize-messages";
import type { Message } from "@/modules/task/types/api";

type UseTaskStreamRecoveryOptions = {
  taskId: string;
  apiMessages: Message[] | undefined;
  messagesReady: boolean;
  streamBody: unknown;
  streamStatus: string;
  sendMessage: (text: string) => void;
  startReconnect: (cursor: number) => void;
  initialMessage?: string | null;
};

export function useTaskStreamRecovery({
  taskId,
  apiMessages,
  messagesReady,
  streamBody,
  streamStatus,
  sendMessage,
  startReconnect,
  initialMessage,
}: UseTaskStreamRecoveryOptions) {
  const initialSentRef = useRef(false);
  const recoveryDoneRef = useRef(false);

  useLayoutEffect(() => {
    const msgCount = apiMessages?.length ?? 0;
    if (initialMessage && !initialSentRef.current && msgCount === 0) {
      initialSentRef.current = true;
      recoveryDoneRef.current = true;
      sendMessage(initialMessage);
    }
  }, [initialMessage, sendMessage, apiMessages?.length]);

  useEffect(() => {
    if (recoveryDoneRef.current || streamBody) return;
    if (streamStatus === "streaming" || streamStatus === "sending") return;
    if (!messagesReady) return;

    let cancelled = false;

    async function recover() {
      const status = await getRunStatus(taskId);
      if (cancelled || recoveryDoneRef.current) return;

      if (status.status === "running") {
        recoveryDoneRef.current = true;
        toast.info("Reconnecting to in-progress generation…");
        startReconnect(0);
        return;
      }

      if (!apiMessages || apiMessages.length === 0) {
        recoveryDoneRef.current = true;
        return;
      }

      const orphan = findOrphanUserMessage(normalizeMessages(apiMessages));
      if (orphan) {
        recoveryDoneRef.current = true;
        toast.info("Resuming interrupted request…");
        sendMessage(orphan);
        return;
      }

      recoveryDoneRef.current = true;
    }

    void recover();

    return () => {
      cancelled = true;
    };
  }, [
    apiMessages,
    messagesReady,
    sendMessage,
    startReconnect,
    streamStatus,
    streamBody,
    taskId,
  ]);

  return { notifyActiveSession: () => { recoveryDoneRef.current = true; } };
}
