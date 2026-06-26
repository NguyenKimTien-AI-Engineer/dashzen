"use client";

import { cn } from "@/lib/utils";
import type { ChatInputVariant } from "@/modules/task/hooks/useChatInput";

type ChatInputTextareaProps = {
  variant: ChatInputVariant;
  value: string;
  placeholder: string;
  disabled: boolean;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
  useTallEmptyLayout: boolean;
  hasUploads: boolean;
  needsScroll: boolean;
  onChange: (value: string) => void;
  onResize: () => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onPaste: (e: React.ClipboardEvent<HTMLTextAreaElement>) => void;
};

export function ChatInputTextarea({
  variant,
  value,
  placeholder,
  disabled,
  textareaRef,
  useTallEmptyLayout,
  hasUploads,
  needsScroll,
  onChange,
  onResize,
  onKeyDown,
  onPaste,
}: ChatInputTextareaProps) {
  return (
    <textarea
      ref={textareaRef}
      value={value}
      onChange={(e) => {
        onChange(e.target.value);
        requestAnimationFrame(onResize);
      }}
      onKeyDown={onKeyDown}
      onPaste={onPaste}
      placeholder={placeholder}
      disabled={disabled}
      rows={1}
      className={cn(
        "resize-none bg-transparent px-4 pt-4 pb-2 text-[15px] leading-relaxed outline-none placeholder:text-muted-foreground/70 disabled:opacity-60",
        needsScroll ? "overflow-y-auto" : "overflow-y-hidden",
        useTallEmptyLayout && "min-h-0 flex-1",
        hasUploads && "min-h-[56px] max-h-[200px] shrink-0 py-2",
        !useTallEmptyLayout && !hasUploads && "shrink-0",
      )}
    />
  );
}
