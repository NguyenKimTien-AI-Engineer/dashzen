import { fetchWithAuth } from "./client";
import type {
  FileArtifact,
  Message,
  MessageAction,
  RunStatus,
  StreamRequest,
  Task,
} from "@/modules/task/types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function createTask(): Promise<Task> {
  const res = await fetchWithAuth("/v1/tasks", { method: "POST", body: "{}" });
  return res.json() as Promise<Task>;
}

export async function listTasks(params?: {
  project_id?: string;
  starred?: boolean;
  unassigned?: boolean;
}): Promise<Task[]> {
  const search = new URLSearchParams();
  if (params?.project_id) search.set("project_id", params.project_id);
  if (params?.starred !== undefined) search.set("starred", String(params.starred));
  if (params?.unassigned) search.set("unassigned", "true");
  const qs = search.toString();
  const res = await fetchWithAuth(`/v1/tasks${qs ? `?${qs}` : ""}`);
  return res.json() as Promise<Task[]>;
}

export async function getTask(id: string): Promise<Task> {
  const res = await fetchWithAuth(`/v1/tasks/${id}`);
  return res.json() as Promise<Task>;
}

export async function updateTask(
  id: string,
  body: { title?: string; status?: string; project_id?: string | null; starred?: boolean },
): Promise<Task> {
  const res = await fetchWithAuth(`/v1/tasks/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
  return res.json() as Promise<Task>;
}

export async function deleteTask(id: string): Promise<void> {
  await fetchWithAuth(`/v1/tasks/${id}`, { method: "DELETE" });
}

export async function getMessages(taskId: string): Promise<Message[]> {
  const res = await fetchWithAuth(`/v1/tasks/${taskId}/messages`);
  return res.json() as Promise<Message[]>;
}

export async function getArtifacts(taskId: string): Promise<FileArtifact[]> {
  const res = await fetchWithAuth(`/v1/tasks/${taskId}/artifacts`);
  return res.json() as Promise<FileArtifact[]>;
}

/** Returns raw Response — caller handles status codes (409, etc.) */
export async function streamTask(
  taskId: string,
  body: StreamRequest,
  signal?: AbortSignal,
): Promise<Response> {
  const url = `${API_URL}/v1/tasks/${taskId}/stream`;
  return fetch(url, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
}

export async function getRunStatus(taskId: string): Promise<RunStatus> {
  const res = await fetchWithAuth(`/v1/tasks/${taskId}/run-status`);
  return res.json() as Promise<RunStatus>;
}

/** Re-attach to a background stream after reload (replay + live events). */
export async function subscribeTaskStream(
  taskId: string,
  cursor = 0,
  signal?: AbortSignal,
): Promise<Response> {
  const url = `${API_URL}/v1/tasks/${taskId}/stream?cursor=${cursor}`;
  return fetch(url, {
    method: "GET",
    credentials: "include",
    signal,
  });
}

export async function stopTask(taskId: string): Promise<void> {
  await fetchWithAuth(`/v1/tasks/${taskId}/stop`, { method: "POST", body: "{}" });
}

export async function getArtifactVersions(taskId: string, name: string): Promise<FileArtifact[]> {
  const res = await fetchWithAuth(
    `/v1/tasks/${taskId}/artifacts/${encodeURIComponent(name)}/versions`,
  );
  return res.json() as Promise<FileArtifact[]>;
}

export async function restoreArtifactVersion(
  taskId: string,
  artifactId: string,
): Promise<FileArtifact> {
  const res = await fetchWithAuth(
    `/v1/tasks/${taskId}/artifacts/${artifactId}/restore`,
    { method: "POST", body: "{}" },
  );
  return res.json() as Promise<FileArtifact>;
}

export async function answerAskGate(
  taskId: string,
  callId: string,
  answer: string,
): Promise<void> {
  await fetchWithAuth(`/v1/tasks/${taskId}/gates/ask`, {
    method: "POST",
    body: JSON.stringify({ call_id: callId, answer }),
  });
}

export async function createMessageAction(
  taskId: string,
  messageId: string,
  body: {
    action: string;
    value?: string;
    metadata?: Record<string, string | number | boolean | null>;
  },
): Promise<MessageAction> {
  const res = await fetchWithAuth(`/v1/tasks/${taskId}/messages/${messageId}/actions`, {
    method: "POST",
    body: JSON.stringify(body),
  });
  return res.json() as Promise<MessageAction>;
}
