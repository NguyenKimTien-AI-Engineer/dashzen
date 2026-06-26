import type { StreamEvent } from "@/modules/task/types/stream-events";
import type { AgentBlockState, TaskState } from "@/modules/task/types/task-state";

export function handleAgentEvent(
  state: TaskState,
  event: StreamEvent,
): Map<string, AgentBlockState> {
  const blocks = new Map(state.agentBlocks);
  if (event.type === "agent_text") {
    const block = blocks.get(event.call_id);
    if (block) {
      blocks.set(event.call_id, {
        ...block,
        textBuffer: block.textBuffer + event.delta,
      });
    }
  } else if (event.type === "agent_think") {
    const block = blocks.get(event.call_id);
    if (block) {
      blocks.set(event.call_id, {
        ...block,
        thinkingBuffer: block.thinkingBuffer + event.delta,
      });
    }
  } else if (event.type === "agent_tool") {
    const block = blocks.get(event.call_id);
    if (block) {
      blocks.set(event.call_id, {
        ...block,
        timeline: [
          ...block.timeline,
          {
            toolCallId: event.tool_call_id,
            name: event.name,
            args: event.args,
            status: "running",
          },
        ],
      });
    }
  } else if (event.type === "agent_result") {
    const block = blocks.get(event.call_id);
    if (block) {
      blocks.set(event.call_id, {
        ...block,
        timeline: block.timeline.map((entry) =>
          entry.toolCallId === event.tool_call_id
            ? {
                ...entry,
                status: event.status,
                result: event.result,
              }
            : entry,
        ),
      });
    }
  }
  return blocks;
}

export function finalizeRunningAgentBlocks(
  agentBlocks: Map<string, AgentBlockState>,
): Map<string, AgentBlockState> {
  const blocks = new Map(agentBlocks);
  for (const [id, block] of blocks) {
    if (block.status === "running") {
      blocks.set(id, { ...block, status: "error" });
    }
  }
  return blocks;
}
