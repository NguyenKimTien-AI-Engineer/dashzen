import { describe, expect, it } from "vitest";
import { composeChatMessages } from "@/modules/task/lib/compose-chat-messages";
import type { DisplayMessage, StreamTurn } from "@/modules/task/types/task-state";

const baseMessage: DisplayMessage = {
  id: "m1",
  role: "user",
  content: "hello",
  status: "sent",
  createdAt: new Date("2026-01-01"),
};

describe("composeChatMessages", () => {
  it("returns persisted messages when no stream turn", () => {
    expect(composeChatMessages([baseMessage], null)).toEqual([baseMessage]);
  });

  it("appends optimistic user when not yet in persisted list", () => {
    const streamTurn: StreamTurn = {
      optimisticUserId: "opt-1",
      optimisticAssistantId: "opt-asst-1",
      userContent: "new question",
      startedAt: Date.now(),
    };
    const result = composeChatMessages([baseMessage], streamTurn);
    expect(result).toHaveLength(2);
    expect(result[1].content).toBe("new question");
    expect(result[1].id).toBe("opt-1");
  });

  it("does not duplicate when the same optimistic id is already present", () => {
    const streamTurn: StreamTurn = {
      optimisticUserId: "m1",
      optimisticAssistantId: "opt-asst-1",
      userContent: "hello",
      startedAt: Date.now(),
    };
    expect(composeChatMessages([baseMessage], streamTurn)).toEqual([baseMessage]);
  });

  it("skips optimistic user when server already persisted the same content", () => {
    const streamTurn: StreamTurn = {
      optimisticUserId: "opt-2",
      optimisticAssistantId: "opt-asst-2",
      userContent: "hello",
      startedAt: Date.now(),
    };
    expect(composeChatMessages([baseMessage], streamTurn)).toEqual([baseMessage]);
  });

  it("allows duplicate content when prior user message is followed by assistant reply", () => {
    const streamTurn: StreamTurn = {
      optimisticUserId: "opt-2",
      optimisticAssistantId: "opt-asst-2",
      userContent: "hello",
      startedAt: Date.now(),
    };
    const persisted: DisplayMessage[] = [
      baseMessage,
      {
        id: "a1",
        role: "assistant",
        content: "Hi there",
        status: "sent",
        createdAt: new Date("2026-01-02"),
      },
    ];
    const result = composeChatMessages(persisted, streamTurn);
    expect(result).toHaveLength(3);
    expect(result[2].id).toBe("opt-2");
  });
});
