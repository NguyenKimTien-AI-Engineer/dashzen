export type Task = {
  id: string;
  title: string | null;
  status: "active" | "archived";
  type: string | null;
  project_id: string | null;
  starred: boolean;
  created_at: string;
  updated_at: string;
};

export type Message = {
  id: string;
  role: "user" | "assistant" | "tool" | "compact";
  content: string;
  parent_id: string | null;
  prompt_tokens: number | null;
  created_at: string;
  activity_log?: import("./activity-log").ActivityLogPayload;
  user_feedback?: "up" | "down" | null;
};

export type MessageAction = {
  id: string;
  task_id: string;
  message_id: string;
  user_id: string;
  action: string;
  value?: string | null;
  metadata_json?: Record<string, unknown> | null;
  created_at: string;
};

export type FileArtifact = {
  id: string;
  name: string;
  source: "workspace" | "upload";
  kind: "text" | "image" | "binary";
  content: string | null;
  size: number;
  message_id?: string | null;
  version?: number;
  is_current?: boolean;
  created_at: string;
};

export type StreamRequest = {
  message: string;
  parent_id?: string | null;
  mode: "auto";
  thinking_enabled?: boolean;
  user_instructions?: string;
  resume?: boolean;
  cursor?: number;
};

export type RunStatus = {
  status: "idle" | "running" | "done" | "error";
  event_count: number;
  started_at: number | null;
};
