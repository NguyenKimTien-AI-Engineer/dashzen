"use client";

import {
  Copy,
  Pencil,
  RefreshCcw,
  ThumbsDown,
  ThumbsUp,
  Volume2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { stripAssistantContent } from "@/modules/task/lib/normalize-messages";
import type { DisplayMessage } from "@/modules/task/types/task-state";
import { MarkdownContent } from "./MarkdownContent";

type ChatMessageProps = {
  message?: DisplayMessage;
  content?: string;
  role?: "user" | "assistant";
  streaming?: boolean;
  showActions?: boolean;
  onCopy?: (message: DisplayMessage) => void;
  onRetry?: (message: DisplayMessage) => void;
  onEditUser?: (message: DisplayMessage) => void;
  onAssistantFeedback?: (message: DisplayMessage, value: "up" | "down") => void;
  onSpeak?: (message: DisplayMessage) => void;
};

function formatTime(value: Date) {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
  }).format(value);
}

export function MessageActions({
  message,
  onCopy,
  onRetry,
  onEditUser,
  onAssistantFeedback,
  onSpeak,
}: {
  message: DisplayMessage;
  onCopy?: (message: DisplayMessage) => void;
  onRetry?: (message: DisplayMessage) => void;
  onEditUser?: (message: DisplayMessage) => void;
  onAssistantFeedback?: (message: DisplayMessage, value: "up" | "down") => void;
  onSpeak?: (message: DisplayMessage) => void;
}) {
  const isUser = message.role === "user";
  return (
    <div
      className={cn(
        "mt-1 flex items-center gap-1 text-muted-foreground",
        isUser ? "justify-end pr-1" : "justify-start",
      )}
    >
      <span className="mr-1 text-xs">{formatTime(message.createdAt)}</span>
      {isUser ? (
        <>
          <Button size="icon-sm" variant="ghost" aria-label="Retry message" onClick={() => onRetry?.(message)}>
            <RefreshCcw className="size-3.5" />
          </Button>
          <Button size="icon-sm" variant="ghost" aria-label="Edit message" onClick={() => onEditUser?.(message)}>
            <Pencil className="size-3.5" />
          </Button>
          <Button size="icon-sm" variant="ghost" aria-label="Copy message" onClick={() => onCopy?.(message)}>
            <Copy className="size-3.5" />
          </Button>
        </>
      ) : (
        <>
          <Button size="icon-sm" variant="ghost" aria-label="Copy response" onClick={() => onCopy?.(message)}>
            <Copy className="size-3.5" />
          </Button>
          <Button size="icon-sm" variant="ghost" aria-label="Read aloud" onClick={() => onSpeak?.(message)}>
            <Volume2 className="size-3.5" />
          </Button>
          <Button
            size="icon-sm"
            variant="ghost"
            aria-label="Helpful response"
            className={message.userFeedback === "up" ? "text-foreground" : undefined}
            onClick={() => onAssistantFeedback?.(message, "up")}
          >
            <ThumbsUp className="size-3.5" />
          </Button>
          <Button
            size="icon-sm"
            variant="ghost"
            aria-label="Not helpful response"
            className={message.userFeedback === "down" ? "text-foreground" : undefined}
            onClick={() => onAssistantFeedback?.(message, "down")}
          >
            <ThumbsDown className="size-3.5" />
          </Button>
          <Button size="icon-sm" variant="ghost" aria-label="Retry response" onClick={() => onRetry?.(message)}>
            <RefreshCcw className="size-3.5" />
          </Button>
        </>
      )}
    </div>
  );
}

export function ChatMessage({
  message,
  content,
  role,
  streaming,
  showActions = true,
  onCopy,
  onRetry,
  onEditUser,
  onAssistantFeedback,
  onSpeak,
}: ChatMessageProps) {
  const resolvedRole = message?.role ?? role ?? "assistant";
  const rawContent = message?.content ?? content ?? "";
  const resolvedContent =
    resolvedRole === "assistant" ? stripAssistantContent(rawContent) : rawContent;
  const isUser = resolvedRole === "user";

  if (!isUser && !resolvedContent.trim()) {
    return null;
  }

  if (isUser) {
    return (
      <div className="py-3">
        <div className="flex justify-end">
          <div className="max-w-[85%] rounded-2xl bg-muted px-4 py-2.5 text-[15px] leading-relaxed whitespace-pre-wrap">
            {resolvedContent}
          </div>
        </div>
        {message && showActions ? (
          <MessageActions
            message={message}
            onCopy={onCopy}
            onRetry={onRetry}
            onEditUser={onEditUser}
            onAssistantFeedback={onAssistantFeedback}
            onSpeak={onSpeak}
          />
        ) : null}
      </div>
    );
  }

  return (
    <div className="py-3">
      <MarkdownContent content={resolvedContent} streaming={streaming} />
      {message && showActions ? (
        <MessageActions
          message={message}
          onCopy={onCopy}
          onRetry={onRetry}
          onEditUser={onEditUser}
          onAssistantFeedback={onAssistantFeedback}
          onSpeak={onSpeak}
        />
      ) : null}
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 py-3">
      <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:0ms]" />
      <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:150ms]" />
      <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:300ms]" />
    </div>
  );
}
