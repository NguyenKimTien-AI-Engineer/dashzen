import { describe, expect, it } from "vitest";
import { normalizeMessages, stripAssistantContent } from "@/modules/task/lib/normalize-messages";
import type { Message } from "@/modules/task/types/api";

function msg(overrides: Partial<Message>): Message {
  return {
    id: "m1",
    role: "user",
    content: "hello",
    parent_id: null,
    prompt_tokens: null,
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("stripAssistantContent", () => {
  it("removes trailing tool_calls JSON", () => {
    const content = 'Done.[{"id":"c1","name":"spawn_agent"}]';
    expect(stripAssistantContent(content)).toBe("Done.");
  });

  it("returns empty when content is only tool-call array", () => {
    expect(stripAssistantContent('[{"id":"c1","name":"spawn_agent"}]')).toBe("");
  });
});

describe("normalizeMessages", () => {
  it("maps API messages to display messages", () => {
    const result = normalizeMessages([
      msg({ id: "u1", role: "user", content: "Hi" }),
      msg({ id: "a1", role: "assistant", content: "Hello" }),
    ]);
    expect(result).toHaveLength(2);
    expect(result[0].role).toBe("user");
    expect(result[1].content).toBe("Hello");
  });

  it("filters out tool role messages", () => {
    const result = normalizeMessages([msg({ role: "tool", content: "x" })]);
    expect(result).toHaveLength(0);
  });
});
