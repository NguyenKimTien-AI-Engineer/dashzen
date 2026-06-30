import { describe, expect, it } from "vitest";
import { QueryClient } from "@tanstack/react-query";
import {
  getLastMessageParentId,
  patchMessageCacheAfterStream,
} from "@/modules/task/lib/patch-message-cache";
import { taskKeys } from "@/modules/task/lib/query-keys";
import type { Message } from "@/modules/task/types/api";

const streamTurn = {
  optimisticUserId: "opt-user-1",
  optimisticAssistantId: "opt-asst-1",
  userContent: "question",
  startedAt: Date.now(),
};

describe("patchMessageCacheAfterStream", () => {
  it("appends user and assistant messages to empty cache", () => {
    const queryClient = new QueryClient();
    const taskId = "task-1";

    patchMessageCacheAfterStream(queryClient, taskId, {
      streamTurn,
      streamingText: "answer text",
    });

    const messages = queryClient.getQueryData<Message[]>(taskKeys.messages(taskId));
    expect(messages).toHaveLength(2);
    expect(messages?.[0].role).toBe("user");
    expect(messages?.[0].id).toBe("opt-user-1");
    expect(messages?.[1].role).toBe("assistant");
    expect(messages?.[1].id).toBe("opt-asst-1");
    expect(messages?.[1].content).toBe("answer text");
  });

  it("skips optimistic user when server already persisted the same content", () => {
    const queryClient = new QueryClient();
    const taskId = "task-2";
    queryClient.setQueryData<Message[]>(taskKeys.messages(taskId), [
      {
        id: "m1",
        role: "user",
        content: "xin chào",
        parent_id: null,
        prompt_tokens: null,
        created_at: "2026-01-01T00:00:00Z",
      },
    ]);

    patchMessageCacheAfterStream(queryClient, taskId, {
      streamTurn: {
        ...streamTurn,
        optimisticUserId: "opt-user-2",
        userContent: "xin chào",
      },
      streamingText: "",
    });

    const messages = queryClient.getQueryData<Message[]>(taskKeys.messages(taskId));
    expect(messages).toHaveLength(1);
    expect(messages?.[0].id).toBe("m1");
  });

  it("allows duplicate user content when the last message is an assistant reply", () => {
    const queryClient = new QueryClient();
    const taskId = "task-2b";
    queryClient.setQueryData<Message[]>(taskKeys.messages(taskId), [
      {
        id: "m1",
        role: "user",
        content: "xin chào",
        parent_id: null,
        prompt_tokens: null,
        created_at: "2026-01-01T00:00:00Z",
      },
      {
        id: "m2",
        role: "assistant",
        content: "Chào bạn",
        parent_id: "m1",
        prompt_tokens: null,
        created_at: "2026-01-02T00:00:00Z",
      },
    ]);

    patchMessageCacheAfterStream(queryClient, taskId, {
      streamTurn: {
        ...streamTurn,
        optimisticUserId: "opt-user-2",
        userContent: "xin chào",
      },
      streamingText: "",
    });

    const messages = queryClient.getQueryData<Message[]>(taskKeys.messages(taskId));
    expect(messages).toHaveLength(3);
    expect(messages?.[2].id).toBe("opt-user-2");
  });

  it("attaches activity_log and usage to optimistic assistant", () => {
    const queryClient = new QueryClient();
    const taskId = "task-3";

    patchMessageCacheAfterStream(queryClient, taskId, {
      streamTurn,
      streamingText: "answer",
      activityLog: {
        type: "activity_log",
        version: 1,
        header_title: "Thinking",
        sections: [
          {
            id: "orchestrator",
            title: "Orchestrator",
            status: "done",
            steps: [
              {
                id: "main-think-0",
                kind: "think",
                label: "",
                status: "success",
                detail: "Planning",
              },
            ],
          },
        ],
      },
      turnUsage: { inputTokens: 1900, outputTokens: 164 },
    });

    const messages = queryClient.getQueryData<Message[]>(taskKeys.messages(taskId));
    const assistant = messages?.find((m) => m.role === "assistant");
    expect(assistant?.activity_log?.usage).toEqual({
      input_tokens: 1900,
      output_tokens: 164,
    });
  });
});

describe("getLastMessageParentId", () => {
  it("returns last assistant id when thread ends with assistant", () => {
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

  it("skips pending user turns after a failed stream", () => {
    const queryClient = new QueryClient();
    const taskId = "task-failed";
    queryClient.setQueryData<Message[]>(taskKeys.messages(taskId), [
      {
        id: "u1",
        role: "user",
        content: "hello",
        parent_id: null,
        prompt_tokens: null,
        created_at: "2026-01-01T00:00:00Z",
      },
      {
        id: "a1",
        role: "assistant",
        content: "hi",
        parent_id: "u1",
        prompt_tokens: null,
        created_at: "2026-01-01T00:01:00Z",
      },
      {
        id: "u2",
        role: "user",
        content: "failed request",
        parent_id: "a1",
        prompt_tokens: null,
        created_at: "2026-01-01T00:02:00Z",
      },
    ]);

    expect(getLastMessageParentId(queryClient, taskId)).toBe("a1");
  });

  it("returns null when cache is empty", () => {
    const queryClient = new QueryClient();
    expect(getLastMessageParentId(queryClient, "empty")).toBeNull();
  });
});
