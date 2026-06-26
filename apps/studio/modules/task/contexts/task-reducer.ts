import type { FileArtifact } from "@/modules/task/types/api";
import type { StreamEvent } from "@/modules/task/types/stream-events";
import {
  finalizeRunningAgentBlocks,
  handleAgentEvent,
} from "@/modules/task/lib/agent-event-handler";
import type { TaskState, ToolCallState } from "@/modules/task/types/task-state";

export type TaskAction =
  | { type: "STREAM_START"; content: string }
  | { type: "STREAM_RECONNECT_START" }
  | { type: "STREAM_DELTA"; delta: string }
  | { type: "STREAM_THINKING_DELTA"; delta: string }
  | { type: "ASK_USER"; callId: string; question: string }
  | { type: "CLEAR_ASK" }
  | {
      type: "TOOL_START";
      callId: string;
      name: string;
      args: Record<string, unknown>;
    }
  | {
      type: "TOOL_RESULT";
      callId: string;
      status: "success" | "rejected" | "error";
      result: string;
    }
  | {
      type: "AGENT_START";
      callId: string;
      name: string;
      displayName: string;
    }
  | { type: "AGENT_EVENT"; event: StreamEvent }
  | {
      type: "AGENT_DONE";
      callId: string;
      status: string;
      summary: string;
    }
  | { type: "TOGGLE_THINKING_PANEL" }
  | {
      type: "STREAM_ARTIFACT";
      id: string;
      name: string;
      content: string;
      kind: string;
      version: number;
    }
  | { type: "SET_TASK_META"; title?: string; taskType?: string }
  | { type: "STREAM_END" }
  | { type: "STREAM_ERROR"; message: string }
  | { type: "SET_ARTIFACTS"; artifacts: FileArtifact[] }
  | { type: "SET_CONNECTION_ERROR"; error: TaskState["error"] }
  | { type: "CLEAR_ERROR" }
  | { type: "RESET" };

function optimisticUserId(): string {
  return `optimistic-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

export function taskReducer(state: TaskState, action: TaskAction): TaskState {
  switch (action.type) {
    case "STREAM_START":
      return {
        ...state,
        streamStatus: "streaming",
        streamKey: state.streamKey + 1,
        streamTurn: {
          optimisticUserId: optimisticUserId(),
          userContent: action.content,
          startedAt: Date.now(),
        },
        streamingText: "",
        thinkingText: "",
        toolCalls: new Map(),
        agentBlocks: new Map(),
        thinkingPanelCollapsed: true,
        error: null,
        lastUserMessage: action.content,
        currentTurnArtifactIds: [],
      };

    case "STREAM_RECONNECT_START":
      return {
        ...state,
        streamStatus: "streaming",
        streamKey: state.streamKey + 1,
        streamingText: "",
        thinkingText: "",
        toolCalls: new Map(),
        agentBlocks: new Map(),
        error: null,
        thinkingPanelCollapsed: true,
        currentTurnArtifactIds: [],
      };

    case "ASK_USER":
      return {
        ...state,
        pendingAsk: { callId: action.callId, question: action.question },
      };

    case "CLEAR_ASK":
      return { ...state, pendingAsk: null };

    case "STREAM_DELTA":
      return {
        ...state,
        streamingText: state.streamingText + action.delta,
      };

    case "STREAM_THINKING_DELTA":
      return {
        ...state,
        thinkingText: state.thinkingText + action.delta,
      };

    case "TOOL_START": {
      const toolCalls = new Map(state.toolCalls);
      toolCalls.set(action.callId, {
        callId: action.callId,
        name: action.name,
        args: action.args,
        status: "running",
      });
      return { ...state, toolCalls };
    }

    case "TOOL_RESULT": {
      const toolCalls = new Map(state.toolCalls);
      const existing = toolCalls.get(action.callId);
      if (existing) {
        toolCalls.set(action.callId, {
          ...existing,
          status: action.status === "success" ? "success" : action.status === "rejected" ? "rejected" : "error",
          result: action.result,
        });
      }
      return { ...state, toolCalls };
    }

    case "AGENT_START": {
      const agentBlocks = new Map(state.agentBlocks);
      agentBlocks.set(action.callId, {
        callId: action.callId,
        name: action.name,
        displayName: action.displayName,
        status: "running",
        summary: "",
        timeline: [],
        textBuffer: "",
        thinkingBuffer: "",
      });
      return { ...state, agentBlocks };
    }

    case "AGENT_EVENT":
      return {
        ...state,
        agentBlocks: handleAgentEvent(state, action.event),
      };

    case "AGENT_DONE": {
      const agentBlocks = new Map(state.agentBlocks);
      const block = agentBlocks.get(action.callId);
      if (block) {
        agentBlocks.set(action.callId, {
          ...block,
          status: action.status === "error" ? "error" : "done",
          summary: action.summary,
        });
      }
      return { ...state, agentBlocks };
    }

    case "TOGGLE_THINKING_PANEL":
      return {
        ...state,
        thinkingPanelCollapsed: !state.thinkingPanelCollapsed,
      };

    case "STREAM_ARTIFACT": {
      const artifacts = new Map(state.artifacts);
      artifacts.set(action.id, {
        id: action.id,
        name: action.name,
        source: "workspace",
        kind: action.kind as "text" | "image" | "binary",
        content: action.content,
        size: action.content.length,
        version: action.version,
        is_current: true,
        created_at: new Date().toISOString(),
      });
      const currentTurnArtifactIds = state.currentTurnArtifactIds.includes(action.id)
        ? state.currentTurnArtifactIds
        : [...state.currentTurnArtifactIds, action.id];
      return { ...state, artifacts, currentTurnArtifactIds };
    }

    case "SET_TASK_META":
      return {
        ...state,
        taskMeta: {
          title: action.title ?? state.taskMeta.title,
          type: action.taskType ?? state.taskMeta.type,
        },
      };

    case "STREAM_END":
      return {
        ...state,
        streamStatus: "idle",
        streamTurn: null,
        streamingText: "",
        thinkingText: "",
        agentBlocks: new Map(),
        thinkingPanelCollapsed: true,
        pendingAsk: null,
        currentTurnArtifactIds: [],
      };

    case "STREAM_ERROR":
      return {
        ...state,
        streamStatus: "error",
        streamingText: "",
        thinkingText: "",
        agentBlocks: finalizeRunningAgentBlocks(state.agentBlocks),
        error: { message: action.message, kind: "stream" },
      };

    case "SET_CONNECTION_ERROR":
      return {
        ...state,
        streamStatus: action.error?.kind === "still_processing" ? "idle" : "error",
        streamingText: action.error?.kind === "still_processing" ? state.streamingText : "",
        thinkingText: action.error?.kind === "still_processing" ? state.thinkingText : "",
        agentBlocks:
          action.error?.kind === "still_processing"
            ? state.agentBlocks
            : finalizeRunningAgentBlocks(state.agentBlocks),
        error: action.error,
      };

    case "CLEAR_ERROR":
      return { ...state, error: null, streamStatus: "idle" };

    case "SET_ARTIFACTS": {
      const artifacts = new Map(state.artifacts);
      for (const artifact of action.artifacts) {
        artifacts.set(artifact.id, artifact);
      }
      return { ...state, artifacts };
    }

    case "RESET":
      return {
        ...state,
        streamStatus: "idle",
        streamKey: 0,
        streamTurn: null,
        streamingText: "",
        thinkingText: "",
        toolCalls: new Map(),
        agentBlocks: new Map(),
        artifacts: new Map(),
        currentTurnArtifactIds: [],
        thinkingPanelCollapsed: true,
        taskMeta: {},
        error: null,
        lastUserMessage: null,
      };

    default:
      return state;
  }
}
