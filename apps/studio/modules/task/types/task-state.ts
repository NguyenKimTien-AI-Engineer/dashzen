import type { FileArtifact } from "./api";
import type { ActivityLogPayload } from "./activity-log";

export type DisplayMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  status: "sent" | "streaming" | "error";
  createdAt: Date;
  activityLog?: ActivityLogPayload;
  artifactIds?: string[];
  hasToolCalls?: boolean;
  userFeedback?: "up" | "down" | null;
};

export type StreamTurn = {
  optimisticUserId: string;
  userContent: string;
  startedAt: number;
};

export type ToolCallState = {
  callId: string;
  name: string;
  args: Record<string, unknown>;
  status: "running" | "success" | "error" | "rejected";
  result?: string;
};

export type AgentTimelineEntry = {
  toolCallId: string;
  name: string;
  args: Record<string, unknown>;
  status: "running" | "success" | "error" | "rejected";
  result?: string;
};

export type AgentBlockState = {
  callId: string;
  name: string;
  displayName: string;
  status: "running" | "done" | "error";
  summary: string;
  timeline: AgentTimelineEntry[];
  textBuffer: string;
  thinkingBuffer: string;
};

export type FileArtifactState = FileArtifact;

export type StreamErrorState = {
  message: string;
  kind?: "connection" | "stream" | "still_processing" | "not_found" | "server_error";
};

export type PendingAsk = {
  callId: string;
  question: string;
};

export type TaskState = {
  taskId: string;
  streamStatus: "idle" | "sending" | "streaming" | "error";
  streamKey: number;
  /** In-flight user turn not yet in API cache */
  streamTurn: StreamTurn | null;
  streamingText: string;
  thinkingText: string;
  toolCalls: Map<string, ToolCallState>;
  agentBlocks: Map<string, AgentBlockState>;
  artifacts: Map<string, FileArtifactState>;
  currentTurnArtifactIds: string[];
  thinkingPanelCollapsed: boolean;
  taskMeta: { title?: string; type?: string };
  error: StreamErrorState | null;
  lastUserMessage: string | null;
  pendingAsk: PendingAsk | null;
};

export const initialTaskState = (taskId: string): TaskState => ({
  taskId,
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
  pendingAsk: null,
});
