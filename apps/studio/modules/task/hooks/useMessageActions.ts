"use client";

import { useCallback, useState } from "react";
import { toast } from "sonner";
import { createMessageAction } from "@/lib/api/tasks";
import type { DisplayMessage } from "@/modules/task/types/task-state";

export function useMessageActions(
  taskId: string,
  messages: DisplayMessage[],
  sendMessage: (text: string) => void,
  onEditUserMessage?: (content: string) => void,
) {
  const [feedbackByMessage, setFeedbackByMessage] = useState<Record<string, "up" | "down">>({});

  const logAction = useCallback(
    async (
      messageId: string,
      action: string,
      value?: string,
      metadata?: Record<string, string | number | boolean | null>,
    ) => {
      try {
        await createMessageAction(taskId, messageId, { action, value, metadata });
      } catch {
        // Keep UI responsive even if analytics logging fails.
      }
    },
    [taskId],
  );

  const handleCopy = useCallback(
    async (msg: DisplayMessage) => {
      try {
        await navigator.clipboard.writeText(msg.content);
        toast.success("Copied");
        await logAction(msg.id, msg.role === "user" ? "user_copy" : "assistant_copy");
      } catch {
        toast.error("Could not copy text");
      }
    },
    [logAction],
  );

  const handleRetry = useCallback(
    async (msg: DisplayMessage) => {
      if (msg.role === "user") {
        sendMessage(msg.content);
        await logAction(msg.id, "user_retry");
        return;
      }
      const idx = messages.findIndex((m) => m.id === msg.id);
      const parentUser = [...messages.slice(0, idx + 1)]
        .reverse()
        .find((m) => m.role === "user");
      if (!parentUser) {
        toast.error("No user prompt found for retry");
        return;
      }
      sendMessage(parentUser.content);
      await logAction(msg.id, "assistant_retry", undefined, { source_user_id: parentUser.id });
    },
    [messages, sendMessage, logAction],
  );

  const handleEditUser = useCallback(
    async (msg: DisplayMessage) => {
      onEditUserMessage?.(msg.content);
      await logAction(msg.id, "user_edit");
    },
    [onEditUserMessage, logAction],
  );

  const handleAssistantFeedback = useCallback(
    async (msg: DisplayMessage, value: "up" | "down") => {
      setFeedbackByMessage((prev) => ({ ...prev, [msg.id]: value }));
      await logAction(msg.id, "assistant_feedback", value);
      toast.success(value === "up" ? "Marked as helpful" : "Feedback saved");
    },
    [logAction],
  );

  const handleSpeak = useCallback(
    async (msg: DisplayMessage) => {
      if (typeof window === "undefined" || !("speechSynthesis" in window)) {
        toast.error("Text-to-speech is not supported in this browser.");
        return;
      }
      const utterance = new SpeechSynthesisUtterance(msg.content);
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utterance);
      await logAction(msg.id, "assistant_tts");
    },
    [logAction],
  );

  return {
    feedbackByMessage,
    handleCopy,
    handleRetry,
    handleEditUser,
    handleAssistantFeedback,
    handleSpeak,
  };
}
