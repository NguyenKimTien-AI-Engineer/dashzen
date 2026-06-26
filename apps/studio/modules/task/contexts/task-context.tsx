"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { answerAskGate, stopTask } from "@/lib/api/tasks";
import { taskKeys } from "@/modules/task/lib/query-keys";
import {
  getLastMessageParentId,
  patchMessageCacheAfterStream,
} from "@/modules/task/lib/patch-message-cache";
import { useTaskMessages } from "@/modules/task/hooks/useTaskMessages";
import { useTaskStreamRecovery } from "@/modules/task/hooks/useTaskStreamRecovery";
import type { StreamRequest, FileArtifact } from "@/modules/task/types/api";
import { initialTaskState } from "@/modules/task/types/task-state";
import { TaskConnection, type StreamConnectionError } from "./task-connection";
import { taskReducer } from "./task-reducer";

type TaskContextValue = {
  sendMessage: (text: string) => void;
  answerAsk: (answer: string) => void;
  stop: () => void;
  retry: () => void;
  clearError: () => void;
  toggleThinkingPanel: () => void;
  syncArtifacts: (artifacts: FileArtifact[]) => void;
  syncTaskMeta: (meta: { title?: string; taskType?: string }) => void;
  state: ReturnType<typeof useTaskState>["state"];
  isStreaming: boolean;
};

type TaskProviderProps = {
  taskId: string;
  children: ReactNode;
  initialMessage?: string | null;
};

function useTaskState(taskId: string) {
  const [state, dispatch] = useReducer(taskReducer, taskId, initialTaskState);
  return { state, dispatch };
}

const TaskContext = createContext<TaskContextValue | null>(null);

export function TaskProvider({ taskId, children, initialMessage }: TaskProviderProps) {
  const { state, dispatch } = useTaskState(taskId);
  const queryClient = useQueryClient();
  const [streamBody, setStreamBody] = useState<StreamRequest | null>(null);
  const [connectionMode, setConnectionMode] = useState<"send" | "subscribe">("send");
  const abortRef = useRef<AbortController | null>(null);
  const streamSnapshotRef = useRef({
    streamTurn: state.streamTurn,
    streamingText: state.streamingText,
  });
  const { data: apiMessages, isSuccess: messagesReady } = useTaskMessages(taskId);

  useEffect(() => {
    streamSnapshotRef.current = {
      streamTurn: state.streamTurn,
      streamingText: state.streamingText,
    };
  }, [state.streamTurn, state.streamingText]);

  const invalidateAfterStream = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: taskKeys.artifacts(taskId) });
    void queryClient.invalidateQueries({ queryKey: taskKeys.all });
    void queryClient.invalidateQueries({ queryKey: taskKeys.detail(taskId) });
  }, [queryClient, taskId]);

  const handleStreamEnd = useCallback(() => {
    patchMessageCacheAfterStream(queryClient, taskId, streamSnapshotRef.current);
    setStreamBody(null);
    setConnectionMode("send");
    void queryClient.refetchQueries({ queryKey: taskKeys.messages(taskId) });
    invalidateAfterStream();
  }, [queryClient, taskId, invalidateAfterStream]);

  const startReconnect = useCallback((cursor: number) => {
    dispatch({ type: "STREAM_RECONNECT_START" });
    setConnectionMode("subscribe");
    setStreamBody({
      message: "",
      mode: "auto",
      resume: true,
      cursor,
    });
  }, []);

  const handleConnectionError = useCallback((error: StreamConnectionError) => {
    if (error.kind === "still_processing") {
      toast.info("Agent is still processing the previous request — please wait.");
      dispatch({
        type: "SET_CONNECTION_ERROR",
        error: { message: error.message, kind: "still_processing" },
      });
      setStreamBody(null);
      return;
    }
    if (error.kind === "not_found") {
      toast.error("Task not found.");
    } else if (error.kind === "unauthorized") {
      toast.error("Session expired. Please sign in again.");
    } else {
      toast.error(error.message);
    }
    dispatch({
      type: "SET_CONNECTION_ERROR",
      error: { message: error.message, kind: error.kind === "network" ? "connection" : "stream" },
    });
    setStreamBody(null);
  }, []);

  const sendMessageRef = useRef<(text: string) => void>(() => {});

  const { notifyActiveSession } = useTaskStreamRecovery({
    taskId,
    apiMessages,
    messagesReady,
    streamBody,
    streamStatus: state.streamStatus,
    sendMessage: (text) => sendMessageRef.current(text),
    startReconnect,
    initialMessage,
  });

  const sendMessage = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || state.streamStatus === "streaming" || state.streamStatus === "sending") {
        return;
      }

      notifyActiveSession();
      const parentId = getLastMessageParentId(queryClient, taskId);
      dispatch({ type: "STREAM_START", content: trimmed });
      setConnectionMode("send");
      setStreamBody({
        message: trimmed,
        mode: "auto",
        parent_id: parentId,
      });
    },
    [notifyActiveSession, queryClient, taskId, state.streamStatus],
  );

  sendMessageRef.current = sendMessage;

  const answerAsk = useCallback(
    (answer: string) => {
      const trimmed = answer.trim();
      if (!trimmed || !state.pendingAsk) return;
      const { callId } = state.pendingAsk;
      dispatch({ type: "CLEAR_ASK" });
      void answerAskGate(taskId, callId, trimmed).catch(() => {
        toast.error("Failed to send answer — please try again.");
      });
    },
    [state.pendingAsk, taskId],
  );

  const stop = useCallback(() => {
    void stopTask(taskId);
    abortRef.current?.abort();
    patchMessageCacheAfterStream(queryClient, taskId, streamSnapshotRef.current);
    dispatch({ type: "STREAM_END" });
    setStreamBody(null);
    void queryClient.refetchQueries({ queryKey: taskKeys.messages(taskId) });
    invalidateAfterStream();
  }, [taskId, queryClient, invalidateAfterStream]);

  const retry = useCallback(() => {
    if (state.lastUserMessage) {
      dispatch({ type: "CLEAR_ERROR" });
      sendMessage(state.lastUserMessage);
    }
  }, [state.lastUserMessage, sendMessage]);

  const clearError = useCallback(() => {
    dispatch({ type: "CLEAR_ERROR" });
  }, []);

  const syncArtifacts = useCallback((artifacts: FileArtifact[]) => {
    dispatch({ type: "SET_ARTIFACTS", artifacts });
  }, []);

  const syncTaskMeta = useCallback((meta: { title?: string; taskType?: string }) => {
    dispatch({ type: "SET_TASK_META", title: meta.title, taskType: meta.taskType });
  }, []);

  const toggleThinkingPanel = useCallback(() => {
    dispatch({ type: "TOGGLE_THINKING_PANEL" });
  }, []);

  useEffect(() => {
    if (state.taskMeta.title) {
      queryClient.setQueryData(taskKeys.detail(taskId), (old: unknown) => {
        if (old && typeof old === "object") {
          return { ...old, title: state.taskMeta.title };
        }
        return old;
      });
      void queryClient.invalidateQueries({ queryKey: taskKeys.all });
    }
  }, [state.taskMeta.title, queryClient, taskId]);

  const isStreaming = state.streamStatus === "streaming" || state.streamStatus === "sending";

  const value = useMemo(
    () => ({
      sendMessage,
      answerAsk,
      stop,
      retry,
      clearError,
      toggleThinkingPanel,
      syncArtifacts,
      syncTaskMeta,
      state,
      isStreaming,
    }),
    [sendMessage, answerAsk, stop, retry, clearError, toggleThinkingPanel, syncArtifacts, syncTaskMeta, state, isStreaming],
  );

  return (
    <TaskContext.Provider value={value}>
      {children}
      {streamBody && (
        <TaskConnection
          key={state.streamKey}
          taskId={taskId}
          body={streamBody}
          mode={connectionMode}
          onEvent={(action) => dispatch(action)}
          onEnd={handleStreamEnd}
          onError={handleConnectionError}
        />
      )}
    </TaskContext.Provider>
  );
}

export function useTaskContext(): TaskContextValue {
  const ctx = useContext(TaskContext);
  if (!ctx) {
    throw new Error("useTaskContext must be used within TaskProvider");
  }
  return ctx;
}
