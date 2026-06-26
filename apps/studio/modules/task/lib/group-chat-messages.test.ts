import { describe, expect, it } from "vitest";
import { groupMessagesForDisplay } from "@/modules/task/lib/group-chat-messages";
import type { DisplayMessage } from "@/modules/task/types/task-state";

function msg(
  id: string,
  role: "user" | "assistant",
  content: string,
): DisplayMessage {
  return {
    id,
    role,
    content,
    status: "sent",
    createdAt: new Date("2026-01-01"),
  };
}

describe("groupMessagesForDisplay", () => {
  it("groups consecutive assistant messages after a user turn", () => {
    const items = groupMessagesForDisplay([
      msg("u1", "user", "Create dashboard"),
      msg("a1", "assistant", "I will build it."),
      msg("a2", "assistant", "Your dashboard is ready."),
    ]);

    expect(items).toHaveLength(2);
    expect(items[0].kind).toBe("user");
    expect(items[1]).toMatchObject({
      kind: "assistant-group",
      content: "I will build it.\n\nYour dashboard is ready.",
      message: { id: "a2" },
    });
  });

  it("starts a new assistant group after the next user message", () => {
    const items = groupMessagesForDisplay([
      msg("u1", "user", "First"),
      msg("a1", "assistant", "Reply one"),
      msg("u2", "user", "Second"),
      msg("a2", "assistant", "Reply two"),
    ]);

    expect(items).toHaveLength(4);
    expect(items.filter((item) => item.kind === "assistant-group")).toHaveLength(2);
  });
});
