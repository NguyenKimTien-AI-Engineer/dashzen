import { describe, expect, it } from "vitest";
import {
  findOrphanUserMessage,
  hasAssistantReply,
  isThreadAwaitingReply,
} from "./detect-orphan-message";
import type { Message } from "@/modules/task/types/api";

function msg(
  partial: Pick<Message, "id" | "role" | "content" | "parent_id" | "created_at">,
): Message {
  return {
    prompt_tokens: null,
    ...partial,
  };
}

describe("findOrphanUserMessage", () => {
  it("returns null when the latest user turn already has an assistant reply", () => {
    const messages: Message[] = [
      msg({
        id: "u1",
        role: "user",
        content: "xin chào",
        parent_id: null,
        created_at: "2026-01-01T10:00:00Z",
      }),
      msg({
        id: "a1",
        role: "assistant",
        content: "Chào bạn!",
        parent_id: "u1",
        created_at: "2026-01-01T10:00:01Z",
      }),
    ];

    expect(isThreadAwaitingReply(messages)).toBe(false);
    expect(findOrphanUserMessage(messages)).toBeNull();
  });

  it("returns user content when no assistant reply exists for the latest user", () => {
    const messages: Message[] = [
      msg({
        id: "u1",
        role: "user",
        content: "xin chào",
        parent_id: null,
        created_at: "2026-01-01T10:00:00Z",
      }),
    ];

    expect(hasAssistantReply(messages, "u1")).toBe(false);
    expect(findOrphanUserMessage(messages)).toBe("xin chào");
  });

  it("does not treat a user as orphan when assistant exists but sorts last in the list", () => {
    const messages: Message[] = [
      msg({
        id: "a1",
        role: "assistant",
        content: "Done",
        parent_id: "u1",
        created_at: "2026-01-01T10:00:02Z",
      }),
      msg({
        id: "u1",
        role: "user",
        content: "xin chào",
        parent_id: null,
        created_at: "2026-01-01T10:00:00Z",
      }),
    ];

    expect(findOrphanUserMessage(messages)).toBeNull();
  });
});
