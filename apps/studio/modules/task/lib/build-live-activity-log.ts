import type { ActivityLogPayload, ActivitySectionPayload, ActivityStepPayload } from "@/modules/task/types/activity-log";
import type { AgentBlockState, ToolCallState } from "@/modules/task/types/task-state";
import { humanizeTool } from "./build-thinking-steps";

function stepsFromBlock(block: AgentBlockState): ActivityStepPayload[] {
  const steps: ActivityStepPayload[] = [];

  const think = block.thinkingBuffer.trim();
  if (think) {
    steps.push({
      id: `${block.callId}-think`,
      kind: "think",
      label: "",
      status: "success",
      detail: think,
    });
  }

  for (const entry of block.timeline) {
    steps.push({
      id: entry.toolCallId,
      kind: "tool",
      label: humanizeTool(entry.name, entry.args),
      status: entry.status,
      detail: entry.result ?? "",
    });
  }

  const text = block.textBuffer.trim();
  const summary = block.summary.trim();
  const outputDuplicate =
    Boolean(summary && text) &&
    (text === summary || text.includes(summary) || summary.includes(text));

  if (text && !outputDuplicate) {
    steps.push({
      id: `${block.callId}-text`,
      kind: "think",
      label: "",
      status: "success",
      detail: text,
    });
  }

  if (summary && block.status !== "running") {
    steps.push({
      id: `${block.callId}-summary`,
      kind: "think",
      label: "",
      status: "success",
      detail: summary,
    });
  }

  return steps;
}

function sectionStatus(
  status: AgentBlockState["status"],
): ActivitySectionPayload["status"] {
  if (status === "running") return "running";
  if (status === "error") return "error";
  return "done";
}

/** Keep the latest section per agent title; orchestrator sections are never collapsed. */
export function collapseActivitySectionsByTitle(
  sections: ActivitySectionPayload[],
): ActivitySectionPayload[] {
  const seen = new Set<string>();
  const result: ActivitySectionPayload[] = [];

  for (let i = sections.length - 1; i >= 0; i -= 1) {
    const section = sections[i];
    if (section.title === "Orchestrator") {
      result.unshift(section);
      continue;
    }
    const key = section.title.trim().toLowerCase();
    if (!key || seen.has(key)) continue;
    seen.add(key);
    result.unshift(section);
  }

  return result;
}

export function buildLiveActivityLog(
  mainThinking: string,
  mainToolCalls: Map<string, ToolCallState>,
  agentBlocks: Map<string, AgentBlockState>,
  headerTitle?: string | null,
): ActivityLogPayload {
  const sections: ActivitySectionPayload[] = [];

  const orchSteps: ActivityStepPayload[] = [];
  const think = mainThinking.trim();
  if (think) {
    orchSteps.push({
      id: "main-think",
      kind: "think",
      label: "",
      status: "success",
      detail: think,
    });
  }
  for (const tool of mainToolCalls.values()) {
    orchSteps.push({
      id: tool.callId,
      kind: "tool",
      label: humanizeTool(tool.name, tool.args),
      status: tool.status,
      detail: tool.result ?? "",
    });
  }

  const anyAgentRunning = Array.from(agentBlocks.values()).some((b) => b.status === "running");
  if (orchSteps.length > 0) {
    sections.push({
      id: "orchestrator",
      title: "Orchestrator",
      status: anyAgentRunning ? "done" : mainToolCalls.size > 0 ? "done" : "running",
      steps: orchSteps,
    });
  }

  for (const block of agentBlocks.values()) {
    sections.push({
      id: block.callId,
      title: block.displayName,
      status: sectionStatus(block.status),
      steps: stepsFromBlock(block),
    });
  }

  return {
    type: "activity_log",
    version: 1,
    header_title: headerTitle?.trim() ?? "",
    sections: collapseActivitySectionsByTitle(sections),
  };
}

export function activityLogHasContent(log: ActivityLogPayload | null | undefined): boolean {
  if (!log) return false;
  return log.sections.some((section) => section.steps.length > 0);
}
