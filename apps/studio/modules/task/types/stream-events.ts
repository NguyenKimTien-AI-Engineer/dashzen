export type MainTextEvent = { type: "main_text"; delta: string };
export type MainThinkEvent = { type: "main_think"; delta: string };
export type MainToolEvent = {
  type: "main_tool";
  call_id: string;
  name: string;
  args: Record<string, unknown>;
};
export type MainResultEvent = {
  type: "main_result";
  call_id: string;
  status: "success" | "rejected" | "error";
  result: string;
};
export type MainAskEvent = {
  type: "main_ask";
  call_id: string;
  question: string;
};
export type AgentStartEvent = {
  type: "agent_start";
  call_id: string;
  name: string;
  display_name: string;
};
export type AgentTextEvent = { type: "agent_text"; call_id: string; delta: string };
export type AgentThinkEvent = { type: "agent_think"; call_id: string; delta: string };
export type AgentToolEvent = {
  type: "agent_tool";
  call_id: string;
  tool_call_id: string;
  name: string;
  args: Record<string, unknown>;
};
export type AgentResultEvent = {
  type: "agent_result";
  call_id: string;
  tool_call_id: string;
  status: "success" | "rejected" | "error";
  result: string;
};
export type AgentDoneEvent = {
  type: "agent_done";
  call_id: string;
  status: string;
  summary: string;
};
export type FileArtifactEvent = {
  type: "file_artifact";
  id?: string;
  name: string;
  content: string;
  kind: string;
  version?: number;
};
export type TaskMetaEvent = {
  type: "task_meta";
  title?: string;
  task_type?: string;
};
export type HeartbeatEvent = { type: "heartbeat" };
export type StreamDoneEvent = {
  type: "stream_done";
  partial_message_id?: string | null;
};
export type StreamErrorEvent = { type: "stream_error"; message: string };

export type StreamEvent =
  | MainTextEvent
  | MainThinkEvent
  | MainToolEvent
  | MainResultEvent
  | MainAskEvent
  | AgentStartEvent
  | AgentTextEvent
  | AgentThinkEvent
  | AgentToolEvent
  | AgentResultEvent
  | AgentDoneEvent
  | FileArtifactEvent
  | TaskMetaEvent
  | HeartbeatEvent
  | StreamDoneEvent
  | StreamErrorEvent;

const KNOWN_TYPES = new Set([
  "main_text",
  "main_think",
  "main_tool",
  "main_result",
  "main_ask",
  "agent_start",
  "agent_text",
  "agent_think",
  "agent_tool",
  "agent_result",
  "agent_done",
  "file_artifact",
  "task_meta",
  "heartbeat",
  "stream_done",
  "stream_error",
]);

export function parseStreamEvent(json: string): StreamEvent | null {
  try {
    const parsed = JSON.parse(json) as { type?: string };
    if (!parsed.type || !KNOWN_TYPES.has(parsed.type)) {
      console.warn("Unknown SSE event type:", parsed.type);
      return null;
    }
    return parsed as StreamEvent;
  } catch {
    return null;
  }
}
