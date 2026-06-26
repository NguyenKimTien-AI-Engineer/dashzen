import { describe, expect, it } from "vitest";
import { handleAgentEvent } from "@/modules/task/lib/agent-event-handler";
import { initialTaskState } from "@/modules/task/types/task-state";
import type { StreamEvent } from "@/modules/task/types/stream-events";

describe("handleAgentEvent", () => {
  const base = initialTaskState("task-1");

  it("appends agent text delta to block buffer", () => {
    const state = {
      ...base,
      agentBlocks: new Map([
        [
          "call-1",
          {
            callId: "call-1",
            name: "planner",
            displayName: "Planner",
            status: "running" as const,
            summary: "",
            timeline: [],
            textBuffer: "Hi",
            thinkingBuffer: "",
          },
        ],
      ]),
    };

    const event: StreamEvent = {
      type: "agent_text",
      call_id: "call-1",
      delta: " there",
    };

    const blocks = handleAgentEvent(state, event);
    expect(blocks.get("call-1")?.textBuffer).toBe("Hi there");
  });
});
