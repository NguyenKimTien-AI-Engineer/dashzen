import { describe, expect, it } from "vitest";
import { QueryClient } from "@tanstack/react-query";
import {
  getLastMessageParentId,
  patchMessageCacheAfterStream,
} from "@/modules/task/lib/patch-message-cache";
import { taskKeys } from "@/modules/task/lib/query-keys";
import type { Message } from "@/modules/task/types/api";

describe("patchMessageCacheAfterStream", () => {
  it("appends user and assistant messages to empty cache", () => {
    const queryClient = new QueryClient();
    const taskId = "task-1";

    patchMessageCacheAfterStream(queryClient, taskId, {
      streamTurn: {
        optimisticUserId: "opt-user",
        userContent: "question",
        startedAt: Date.now(),
      },
      streamingText: "answer text",
    });

    const messages = queryClient.getQueryData<Message[]>(taskKeys.messages(taskId));
    expect(messages).toHaveLength(2);
    expect(messages?.[0].role).toBe("user");
    expect(messages?.[1].role).toBe("assistant");
    expect(messages?.[1].content).toBe("answer text");
  });

  it("does not duplicate existing user content", () => {
    const queryClient = new QueryClient();
    const taskId = "task-2";
    queryClient.setQueryData<Message[]>(taskKeys.messages(taskId), [
      {
        id: "m1",
        role: "user",
        content: "question",
        parent_id: null,
        prompt_tokens: null,
        created_at: "2026-01-01T00:00:00Z",
      },
    ]);

    patchMessageCacheAfterStream(queryClient, taskId, {
      streamTurn: {
        optimisticUserId: "opt-user",
        userContent: "question",
        startedAt: Date.now(),
      },
      streamingText: "",
    });

    const messages = queryClient.getQueryData<Message[]>(taskKeys.messages(taskId));
    expect(messages).toHaveLength(1);
  });
});

describe("getLastMessageParentId", () => {
  it("returns last message id", () => {
    const queryClient = new QueryClient();
    const taskId = "task-3";
    queryClient.setQueryData<Message[]>(taskKeys.messages(taskId), [
      {
        id: "m1",
        role: "user",
        content: "a",
        parent_id: null,
        prompt_tokens: null,
        created_at: "2026-01-01T00:00:00Z",
      },
      {
        id: "m2",
        role: "assistant",
        content: "b",
        parent_id: "m1",
        prompt_tokens: null,
        created_at: "2026-01-02T00:00:00Z",
      },
    ]);

    expect(getLastMessageParentId(queryClient, taskId)).toBe("m2");
  });

  it("returns null when cache is empty", () => {
    const queryClient = new QueryClient();
    expect(getLastMessageParentId(queryClient, "empty")).toBeNull();
  });
});
