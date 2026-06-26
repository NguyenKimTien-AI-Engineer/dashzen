"use client";

import { useMemo } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useChatDisplayMessages } from "@/modules/task/hooks/useChatDisplayMessages";
import { useMessageActions } from "@/modules/task/hooks/useMessageActions";
import { useTask } from "@/modules/task/hooks/useTask";
import { useStreamScroll } from "@/modules/task/hooks/useStreamScroll";
import { useTaskDetail } from "@/modules/task/hooks/useTaskMeta";
import {
  activityLogHasContent,
  buildLiveActivityLog,
} from "@/modules/task/lib/build-live-activity-log";
import {
  getAssistantGroupActivityLog,
} from "@/modules/task/lib/activity-log-panel";
import {
  groupMessagesForDisplay,
} from "@/modules/task/lib/group-chat-messages";
import {
  groupArtifactsByMessage,
  resolveGroupArtifacts,
} from "@/modules/task/lib/chat-artifacts";
import type { FileArtifact } from "@/modules/task/types/api";
import { ChatMessage, MessageActions, TypingIndicator } from "./ChatMessage";
import { ThinkingPanel } from "./ActivityBlocks";
import { MessageArtifacts } from "./MessageArtifacts";
import { CHAT_COLUMN_CLASS } from "./chat-layout";

type ChatMessageListProps = {
  taskId: string;
  onEditUserMessage?: (content: string) => void;
};

export function ChatMessageList({ taskId, onEditUserMessage }: ChatMessageListProps) {
  const {
    sendMessage,
    streamingText,
    thinkingText,
    toolCalls,
    agentBlocks,
    thinkingPanelCollapsed,
    taskMeta,
    artifacts,
    currentTurnArtifactIds,
    streamError,
    isStreaming,
    retry,
    clearError,
    toggleThinkingPanel,
  } = useTask();
  const messages = useChatDisplayMessages(taskId);

  const {
    feedbackByMessage,
    handleCopy,
    handleRetry,
    handleEditUser,
    handleAssistantFeedback,
    handleSpeak,
  } = useMessageActions(taskId, messages, sendMessage, onEditUserMessage);

  const { data: task } = useTaskDetail(taskId);
  const dashboardTitle =
    task?.title && task.title.trim() && task.title !== "New chat"
      ? task.title.trim()
      : "Dashboard";

  const artifactsByMessage = useMemo(
    () => groupArtifactsByMessage(artifacts.values()),
    [artifacts],
  );

  const liveArtifacts = useMemo(
    () =>
      currentTurnArtifactIds
        .map((id) => artifacts.get(id))
        .filter((artifact): artifact is FileArtifact => Boolean(artifact)),
    [artifacts, currentTurnArtifactIds],
  );

  const liveActivityLog = useMemo(
    () =>
      buildLiveActivityLog(
        thinkingText,
        toolCalls,
        agentBlocks,
        taskMeta.title ?? task?.title,
      ),
    [thinkingText, toolCalls, agentBlocks, taskMeta.title, task?.title],
  );

  const displayItems = useMemo(
    () => groupMessagesForDisplay(messages),
    [messages],
  );

  const showLiveThinking =
    isStreaming && activityLogHasContent(liveActivityLog);

  const hasRunningAgents = Array.from(agentBlocks.values()).some(
    (block) => block.status === "running",
  );

  const { containerRef, bottomRef } = useStreamScroll([
    displayItems,
    messages,
    streamingText,
    agentBlocks.size,
    toolCalls.size,
    thinkingPanelCollapsed,
    artifacts.size,
    currentTurnArtifactIds.length,
  ]);

  const hasContent =
    messages.length > 0 ||
    streamingText ||
    showLiveThinking ||
    liveArtifacts.length > 0;

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto"
      role="log"
      aria-live="polite"
    >
      {!hasContent && !isStreaming && (
        <div
          className={cn(
            "flex h-full items-center justify-center py-12 text-sm text-muted-foreground",
            CHAT_COLUMN_CLASS,
          )}
        >
          Send your first message to get started
        </div>
      )}

      <div className={cn("pb-6", CHAT_COLUMN_CLASS)}>
        {displayItems.map((item, itemIndex) => {
          if (item.kind === "user") {
            return (
              <div key={item.message.id}>
                <ChatMessage
                  message={{
                    ...item.message,
                    userFeedback:
                      feedbackByMessage[item.message.id] ??
                      item.message.userFeedback ??
                      null,
                  }}
                  onCopy={handleCopy}
                  onRetry={handleRetry}
                  onEditUser={handleEditUser}
                  onAssistantFeedback={handleAssistantFeedback}
                  onSpeak={handleSpeak}
                />
              </div>
            );
          }

          const activityLog = getAssistantGroupActivityLog(item.messages);
          const messageArtifacts = resolveGroupArtifacts(
            item.messages.map((message) => message.id),
            artifactsByMessage,
            artifacts,
          );
          const isLastItem = itemIndex === displayItems.length - 1;
          const showActions =
            Boolean(item.content.trim()) && (!isStreaming || !isLastItem);
          const assistantMessage = {
            ...item.message,
            content: item.content,
            userFeedback:
              feedbackByMessage[item.message.id] ??
              item.message.userFeedback ??
              null,
          };

          return (
            <div key={item.message.id}>
              {activityLog ? (
                <ThinkingPanel activityLog={activityLog} defaultCollapsed />
              ) : null}
              {item.content.trim() ? (
                <ChatMessage message={assistantMessage} showActions={false} />
              ) : null}
              {messageArtifacts.length > 0 ? (
                <MessageArtifacts
                  taskId={taskId}
                  artifacts={messageArtifacts}
                  dashboardTitle={dashboardTitle}
                />
              ) : null}
              {showActions ? (
                <MessageActions
                  message={assistantMessage}
                  onCopy={handleCopy}
                  onRetry={handleRetry}
                  onEditUser={handleEditUser}
                  onAssistantFeedback={handleAssistantFeedback}
                  onSpeak={handleSpeak}
                />
              ) : null}
            </div>
          );
        })}

        {showLiveThinking ? (
          <ThinkingPanel
            activityLog={liveActivityLog}
            isActive={hasRunningAgents || Boolean(thinkingText.trim())}
            collapsed={thinkingPanelCollapsed}
            onToggle={toggleThinkingPanel}
          />
        ) : null}

        {liveArtifacts.length > 0 ? (
          <MessageArtifacts
            taskId={taskId}
            artifacts={liveArtifacts}
            dashboardTitle={dashboardTitle}
          />
        ) : null}

        {isStreaming && !streamingText && !showLiveThinking && <TypingIndicator />}

        {streamingText && (
          <ChatMessage
            role="assistant"
            content={streamingText}
            streaming={isStreaming && !hasRunningAgents}
          />
        )}

        {streamError && streamError.kind !== "still_processing" && (
          <div className="my-4 rounded-xl border border-destructive/30 bg-destructive/5 p-4">
            <p className="text-sm text-destructive">{streamError.message}</p>
            <div className="mt-3 flex gap-2">
              <Button size="sm" variant="outline" onClick={retry}>
                Retry
              </Button>
              <Button size="sm" variant="ghost" onClick={clearError}>
                Dismiss
              </Button>
            </div>
          </div>
        )}
      </div>

      <div ref={bottomRef} className="h-1" />
    </div>
  );
}
