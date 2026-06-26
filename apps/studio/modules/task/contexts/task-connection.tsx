"use client";

import { useEffect, useRef } from "react";
import { parseStreamEvent } from "@/modules/task/types/stream-events";
import type { StreamRequest } from "@/modules/task/types/api";
import { streamTask, subscribeTaskStream } from "@/lib/api/tasks";
import { mapStreamEventToAction } from "@/modules/task/lib/map-stream-event";
import type { StreamEvent } from "@/modules/task/types/stream-events";
import type { TaskAction } from "./task-reducer";

export type StreamConnectionError = {
  kind: "still_processing" | "not_found" | "server_error" | "network" | "unauthorized";
  message: string;
};

type TaskConnectionProps = {
  taskId: string;
  body: StreamRequest;
  mode?: "send" | "subscribe";
  onEvent: (action: TaskAction) => void;
  onEnd: () => void;
  onError: (error: StreamConnectionError) => void;
};

export function parseSSEBuffer(buffer: string): { events: StreamEvent[]; remainder: string } {
  const events: StreamEvent[] = [];
  const parts = buffer.split("\n\n");
  const remainder = parts.pop() ?? "";

  for (const part of parts) {
    for (const line of part.split("\n")) {
      if (line.startsWith("data:")) {
        const json = line.slice(5).trim();
        const event = parseStreamEvent(json);
        if (event) events.push(event);
      }
    }
  }

  return { events, remainder };
}

export function TaskConnection({
  taskId,
  body,
  mode = "send",
  onEvent,
  onEnd,
  onError,
}: TaskConnectionProps) {
  const onEventRef = useRef(onEvent);
  const onEndRef = useRef(onEnd);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onEventRef.current = onEvent;
    onEndRef.current = onEnd;
    onErrorRef.current = onError;
  });

  useEffect(() => {
    const abortController = new AbortController();
    let ended = false;

    async function connect() {
      try {
        const response =
          mode === "subscribe"
            ? await subscribeTaskStream(taskId, body.cursor ?? 0, abortController.signal)
            : await streamTask(taskId, body, abortController.signal);

        if (response.status === 401) {
          onErrorRef.current({
            kind: "unauthorized",
            message: "Session expired. Please sign in again.",
          });
          return;
        }
        if (response.status === 409) {
          onErrorRef.current({
            kind: "still_processing",
            message: "Agent is still processing the previous request.",
          });
          return;
        }
        if (response.status === 404) {
          onErrorRef.current({ kind: "not_found", message: "Task not found." });
          return;
        }
        if (!response.ok) {
          onErrorRef.current({
            kind: "server_error",
            message: `Server error (${response.status}).`,
          });
          return;
        }

        const reader = response.body?.getReader();
        if (!reader) {
          onErrorRef.current({ kind: "network", message: "No response stream." });
          return;
        }

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const { events, remainder } = parseSSEBuffer(buffer);
          buffer = remainder;

          for (const event of events) {
            if (event.type === "stream_done") {
              ended = true;
              onEndRef.current();
              onEventRef.current({ type: "STREAM_END" });
              return;
            }
            if (event.type === "stream_error") {
              ended = true;
              onEndRef.current();
              onEventRef.current({ type: "STREAM_ERROR", message: event.message });
              return;
            }
            const action = mapStreamEventToAction(event);
            if (action) onEventRef.current(action);
          }
        }

        if (!ended) {
          onEndRef.current();
          onEventRef.current({ type: "STREAM_END" });
        }
      } catch (err) {
        if (abortController.signal.aborted) return;
        onErrorRef.current({
          kind: "network",
          message: err instanceof Error ? err.message : "Connection failed.",
        });
      }
    }

    void connect();

    return () => {
      abortController.abort();
    };
  }, [taskId, mode, JSON.stringify(body)]);

  return null;
}
