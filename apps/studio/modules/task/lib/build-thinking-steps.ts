import type { AgentBlockState, AgentTimelineEntry, ToolCallState } from "@/modules/task/types/task-state";

export type ThinkingStep =
  | {
      id: string;
      kind: "think";
      text: string;
      isStreaming?: boolean;
    }
  | {
      id: string;
      kind: "tool";
      label: string;
      status: AgentTimelineEntry["status"];
      detail?: string;
    };

export function humanizeTool(name: string, args: Record<string, unknown>): string {
  const path = typeof args.path === "string" ? args.path : "";
  switch (name) {
    case "read_file":
      return path ? `Read ${path}` : "Read file";
    case "write_file":
      return path ? `Write ${path}` : "Write file";
    case "edit_file":
      return path ? `Edit ${path}` : "Edit file";
    case "list_file":
      return "List workspace files";
    case "set_memory":
      return "Configure workflow memory";
    case "csv_preview":
      return "Preview CSV data";
    case "schema_inspector":
      return "Inspect data schema";
    case "search_components":
      return "Search UI components";
    case "spawn_agent":
      return typeof args.name === "string" ? `Run ${args.name}` : "Run agent";
    default:
      return name.replace(/_/g, " ");
  }
}

function toolStatus(
  status: ToolCallState["status"],
): AgentTimelineEntry["status"] {
  return status;
}

export function buildThinkingSteps(
  mainThinking: string,
  mainToolCalls: Map<string, ToolCallState>,
  agentBlocks: Map<string, AgentBlockState>,
): ThinkingStep[] {
  const steps: ThinkingStep[] = [];

  const orchestratorThink = mainThinking.trim();
  if (orchestratorThink) {
    steps.push({
      id: "main-think",
      kind: "think",
      text: orchestratorThink,
      isStreaming: true,
    });
  }

  for (const tool of mainToolCalls.values()) {
    steps.push({
      id: `main-tool-${tool.callId}`,
      kind: "tool",
      label: humanizeTool(tool.name, tool.args),
      status: toolStatus(tool.status),
      detail: tool.result,
    });
  }

  for (const block of agentBlocks.values()) {
    const think = block.thinkingBuffer.trim();
    if (think) {
      steps.push({
        id: `${block.callId}-think`,
        kind: "think",
        text: think,
        isStreaming: block.status === "running",
      });
    }

    for (const entry of block.timeline) {
      steps.push({
        id: `${block.callId}-${entry.toolCallId}`,
        kind: "tool",
        label: humanizeTool(entry.name, entry.args),
        status: entry.status,
        detail: entry.result,
      });
    }

    const text = block.textBuffer.trim();
    if (text) {
      steps.push({
        id: `${block.callId}-text`,
        kind: "think",
        text,
        isStreaming: block.status === "running",
      });
    }
  }

  return steps;
}

export function getThinkingPreview(steps: ThinkingStep[]): string | null {
  if (steps.length === 0) return null;
  const last = steps[steps.length - 1];
  if (last.kind === "tool") return last.label;
  const firstLine = last.text.split("\n").find((line) => line.trim())?.trim();
  if (!firstLine) return null;
  return firstLine.length > 120 ? `${firstLine.slice(0, 120)}…` : firstLine;
}

export function hasThinkingActivity(
  mainThinking: string,
  mainToolCalls: Map<string, ToolCallState>,
  agentBlocks: Map<string, AgentBlockState>,
): boolean {
  if (mainThinking.trim()) return true;
  if (mainToolCalls.size > 0) return true;
  if (agentBlocks.size > 0) return true;
  return false;
}
