"use client";

import { useEffect, useLayoutEffect, useRef } from "react";
import { toast } from "sonner";
import { getRunStatus } from "@/lib/api/tasks";
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
      try {
        const status = await getRunStatus(taskId);
        if (cancelled || recoveryDoneRef.current) return;

        // Only re-attach when the server still has an active stream (e.g. page reload
        // mid-generation). Do not auto-resend failed/orphan user messages on chat reopen —
        // the user can retry manually via the error toast or by sending again.
        if (status.status === "running") {
          recoveryDoneRef.current = true;
          toast.info("Reconnecting to in-progress generation…");
          startReconnect(0);
          return;
        }
      } catch {
        // API unreachable — skip recovery so opening a chat never crashes the UI.
      }

      recoveryDoneRef.current = true;
    }

    void recover();

    return () => {
      cancelled = true;
    };
  }, [
    messagesReady,
    sendMessage,
    startReconnect,
    streamStatus,
    streamBody,
    taskId,
  ]);

  return { notifyActiveSession: () => { recoveryDoneRef.current = true; } };
}
