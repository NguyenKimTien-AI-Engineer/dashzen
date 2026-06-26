"use client";

import { ChatAskPrompt } from "./ChatAskPrompt";
import { ChatInput } from "./ChatInput";
import { ChatMessageList } from "./ChatMessageList";
import { TaskHeader } from "./TaskHeader";
import { ArtifactCanvasShell } from "../canvas/ArtifactCanvasShell";
import { useProjects } from "@/modules/project/hooks/useProjects";
import { createProject } from "@/lib/api/projects";
import { updateTask } from "@/lib/api/tasks";
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useArtifactCanvasStore } from "@/lib/stores/artifactCanvasStore";
import { taskKeys } from "@/modules/task/lib/query-keys";
import { projectKeys } from "@/modules/project/lib/query-keys";
import { useTask } from "@/modules/task/hooks/useTask";
import { TaskArtifactsSync } from "@/modules/task/hooks/useTaskArtifacts";
import { TaskMetaSync } from "@/modules/task/hooks/useTaskMeta";

type ChatWorkspaceProps = {
  taskId: string;
};

export function ChatWorkspace({ taskId }: ChatWorkspaceProps) {
  const queryClient = useQueryClient();
  const { sendMessage, answerAsk, stop, isStreaming, pendingAsk } = useTask();
  const { data: projects = [] } = useProjects();
  const closeCanvas = useArtifactCanvasStore((state) => state.closeCanvas);
  const [draftText, setDraftText] = useState("");
  const [draftVersion, setDraftVersion] = useState(0);

  useEffect(() => {
    return () => closeCanvas();
  }, [taskId, closeCanvas]);

  async function handleSelectProject(projectId: string | null) {
    try {
      await updateTask(taskId, { project_id: projectId });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: taskKeys.detail(taskId) }),
        queryClient.invalidateQueries({ queryKey: taskKeys.all }),
        queryClient.invalidateQueries({ queryKey: projectKeys.all }),
      ]);
      toast.success(projectId ? "Added to project" : "Removed from project");
    } catch {
      toast.error("Could not update project");
    }
  }

  async function handleCreateProject(name: string) {
    const trimmed = name.trim();
    if (!trimmed) return;
    try {
      const project = await createProject(trimmed);
      await handleSelectProject(project.id);
    } catch {
      toast.error("Could not create project");
    }
  }

  function handleMicClick() {
    toast.info("Microphone input will be enabled in a next update.");
  }

  function handleVoiceClick() {
    toast.info("Voice conversation mode is coming soon.");
  }

  function handleEditUserMessage(content: string) {
    setDraftText(content);
    setDraftVersion((v) => v + 1);
    toast.info("Loaded message into composer for editing.");
  }

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      <TaskArtifactsSync taskId={taskId} />
      <TaskMetaSync taskId={taskId} />
      {/* ArtifactCanvasShell wraps the full height so the canvas panel
          is not clipped by TaskHeader — header lives inside the left column */}
      <ArtifactCanvasShell>
        <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <TaskHeader taskId={taskId} />
          <ChatMessageList
            taskId={taskId}
            onEditUserMessage={handleEditUserMessage}
          />
          {pendingAsk ? (
            <ChatAskPrompt
              question={pendingAsk.question}
              onAnswer={answerAsk}
            />
          ) : (
            <ChatInput
              onSend={sendMessage}
              onStop={stop}
              isStreaming={isStreaming}
              placeholder="Write a message..."
              autoFocus
              variant="chat"
              externalDraft={draftText}
              externalDraftVersion={draftVersion}
              projects={projects}
              onSelectProject={(projectId) => {
                void handleSelectProject(projectId);
              }}
              onCreateProject={handleCreateProject}
              onMicClick={handleMicClick}
              onVoiceClick={handleVoiceClick}
            />
          )}
        </div>
      </ArtifactCanvasShell>
    </div>
  );
}
