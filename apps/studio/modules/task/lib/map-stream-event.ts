import type { StreamEvent } from "@/modules/task/types/stream-events";
import type { TaskAction } from "../contexts/task-reducer";

export function mapStreamEventToAction(event: StreamEvent): TaskAction | null {
  switch (event.type) {
    case "main_text":
      return { type: "STREAM_DELTA", delta: event.delta };
    case "main_think":
      return { type: "STREAM_THINKING_DELTA", delta: event.delta };
    case "main_tool":
      return {
        type: "TOOL_START",
        callId: event.call_id,
        name: event.name,
        args: event.args,
      };
    case "main_result":
      return {
        type: "TOOL_RESULT",
        callId: event.call_id,
        status: event.status,
        result: event.result,
      };
    case "agent_start":
      return {
        type: "AGENT_START",
        callId: event.call_id,
        name: event.name,
        displayName: event.display_name,
      };
    case "agent_text":
      return { type: "AGENT_EVENT", event };
    case "agent_think":
      return { type: "AGENT_EVENT", event };
    case "agent_tool":
      return { type: "AGENT_EVENT", event };
    case "agent_result":
      return { type: "AGENT_EVENT", event };
    case "agent_done":
      return {
        type: "AGENT_DONE",
        callId: event.call_id,
        status: event.status,
        summary: event.summary,
      };
    case "file_artifact":
      return {
        type: "STREAM_ARTIFACT",
        id: event.id || `${event.name}-${event.version ?? 1}`,
        name: event.name,
        content: event.content,
        kind: event.kind,
        version: event.version ?? 1,
      };
    case "task_meta":
      return {
        type: "SET_TASK_META",
        title: event.title,
        taskType: event.task_type,
      };
    case "main_ask":
      return { type: "ASK_USER", callId: event.call_id, question: event.question };
    case "stream_done":
      return { type: "STREAM_END" };
    case "stream_error":
      return { type: "STREAM_ERROR", message: event.message };
    case "heartbeat":
      return null;
    default:
      return null;
  }
}
