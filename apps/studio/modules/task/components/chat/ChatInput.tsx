"use client";

import { cn } from "@/lib/utils";
import type { Project } from "@/modules/project/types/api";
import { useChatInput } from "@/modules/task/hooks/useChatInput";
import { CHAT_COLUMN_CLASS } from "./chat-layout";
import { ChatUploadPreview } from "./ChatUploadPreview";
import { ChatInputTextarea } from "./ChatInputTextarea";
import { ChatInputToolbar } from "./ChatInputToolbar";

type ChatInputProps = {
  onSend: (text: string) => void;
  onStop?: () => void;
  isStreaming?: boolean;
  disabled?: boolean;
  placeholder?: string;
  autoFocus?: boolean;
  className?: string;
  variant?: "home" | "chat";
  defaultValue?: string;
  onFilesSelected?: (files: File[]) => void;
  projects?: Project[];
  selectedProjectId?: string | null;
  onSelectProject?: (projectId: string | null) => void;
  onCreateProject?: (name: string) => Promise<void> | void;
  onMicClick?: () => void;
  onVoiceClick?: () => void;
  externalDraft?: string;
  externalDraftVersion?: number;
};

export function ChatInput({
  onSend,
  onStop,
  isStreaming = false,
  disabled = false,
  placeholder = "How can I help you today?",
  autoFocus = false,
  className,
  variant = "chat",
  defaultValue = "",
  onFilesSelected,
  projects = [],
  selectedProjectId = null,
  onSelectProject,
  onCreateProject,
  onMicClick,
  onVoiceClick,
  externalDraft,
  externalDraftVersion,
}: ChatInputProps) {
  const input = useChatInput({
    variant,
    defaultValue,
    autoFocus,
    isStreaming,
    disabled,
    onSend,
    onFilesSelected,
    externalDraft,
    externalDraftVersion,
  });

  return (
    <div
      className={cn(
        "w-full",
        variant === "home" ? "mx-auto max-w-2xl" : CHAT_COLUMN_CLASS,
        variant === "home" ? undefined : "pb-4",
        className,
      )}
    >
      <div
        className={cn(
          "relative overflow-hidden rounded-2xl bg-card shadow-sm ring-1 ring-border/20 transition-shadow focus-within:shadow-md focus-within:ring-border/30",
          variant === "home" && "rounded-3xl",
        )}
      >
        <div
          className={cn(
            "flex flex-col",
            input.useTallEmptyLayout &&
              (input.isHome ? "h-[128px] max-h-[128px]" : "h-[88px] max-h-[88px]"),
            input.useExpandedLayout && "max-h-[min(60vh,560px)]",
          )}
        >
          {input.hasUploads && (
            <div className="flex shrink-0 gap-2.5 overflow-x-auto px-4 pt-3 pb-2">
              {input.uploads.map((upload) => (
                <ChatUploadPreview
                  key={upload.id}
                  upload={upload}
                  size={variant}
                  onRemove={input.removeUpload}
                />
              ))}
            </div>
          )}
          <ChatInputTextarea
            variant={variant}
            value={input.text}
            placeholder={placeholder}
            disabled={isStreaming || disabled}
            textareaRef={input.textareaRef}
            useTallEmptyLayout={input.useTallEmptyLayout}
            hasUploads={input.hasUploads}
            needsScroll={input.needsScroll}
            onChange={input.setText}
            onResize={input.resizeTextarea}
            onKeyDown={input.handleKeyDown}
            onPaste={input.handlePaste}
          />
          <ChatInputToolbar
            fileInputRef={input.fileInputRef}
            canSend={input.canSend}
            isStreaming={isStreaming}
            disabled={disabled}
            onSend={input.handleSend}
            onStop={onStop}
            onMicClick={onMicClick}
            onVoiceClick={onVoiceClick}
            projects={projects}
            selectedProjectId={selectedProjectId}
            onSelectProject={onSelectProject}
            onCreateProject={onCreateProject}
          />
        </div>
      </div>
      <input
        ref={input.fileInputRef}
        type="file"
        className="hidden"
        multiple
        accept="image/*,.pdf,.csv,.xlsx,.xls,.txt,.md,.doc,.docx,.ppt,.pptx,.json,.xml,.yaml,.yml"
        onChange={(e) => {
          const files = Array.from(e.target.files ?? []);
          input.handleLocalFilesSelected(files);
          e.currentTarget.value = "";
        }}
      />
      {variant === "chat" && (
        <p className="mt-2 text-center text-xs text-muted-foreground">
          DashZen is AI and can make mistakes. Please double-check responses.
        </p>
      )}
    </div>
  );
}
