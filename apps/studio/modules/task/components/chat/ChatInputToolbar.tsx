"use client";

import { ArrowUp, AudioLines, Loader2, Mic, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatInputActionsMenu } from "./ChatInputActionsMenu";
import type { Project } from "@/modules/project/types/api";

type ChatInputToolbarProps = {
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  canSend: boolean;
  isStreaming: boolean;
  disabled: boolean;
  onSend: () => void;
  onStop?: () => void;
  onMicClick?: () => void;
  onVoiceClick?: () => void;
  projects?: Project[];
  selectedProjectId?: string | null;
  onSelectProject?: (projectId: string | null) => void;
  onCreateProject?: (name: string) => Promise<void> | void;
};

export function ChatInputToolbar({
  fileInputRef,
  canSend,
  isStreaming,
  disabled,
  onSend,
  onStop,
  onMicClick,
  onVoiceClick,
  projects,
  selectedProjectId,
  onSelectProject,
  onCreateProject,
}: ChatInputToolbarProps) {
  return (
    <div className="flex shrink-0 items-center justify-between gap-2 px-3 pb-3 pt-1">
      <div className="flex items-center gap-1.5">
        <ChatInputActionsMenu
          fileInputRef={fileInputRef}
          projects={projects}
          selectedProjectId={selectedProjectId}
          onSelectProject={onSelectProject}
          onCreateProject={onCreateProject}
        />
      </div>
      <div className="flex items-center gap-1.5">
        <Button
          type="button"
          size="icon-sm"
          variant="ghost"
          className="rounded-full text-muted-foreground hover:text-foreground"
          aria-label="Microphone"
          onClick={onMicClick}
        >
          <Mic className="size-4" />
        </Button>
        <Button
          type="button"
          size="icon-sm"
          variant="ghost"
          className="rounded-full text-muted-foreground hover:text-foreground"
          aria-label="Voice conversation"
          onClick={onVoiceClick}
        >
          <AudioLines className="size-4" />
        </Button>
        {isStreaming && onStop ? (
          <Button
            type="button"
            size="icon-sm"
            variant="outline"
            onClick={onStop}
            aria-label="Stop"
            className="rounded-full"
          >
            <Square className="size-3.5 fill-current" />
          </Button>
        ) : (
          <Button
            type="button"
            size="icon-sm"
            onClick={onSend}
            disabled={!canSend}
            aria-label="Send message"
            className="rounded-full"
          >
            {disabled && !isStreaming ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <ArrowUp className="size-4" />
            )}
          </Button>
        )}
      </div>
    </div>
  );
}
