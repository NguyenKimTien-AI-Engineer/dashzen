import { getTaskDisplayTitle } from "@/modules/chats/lib/format-relative-time";
import type { ArtifactListItem } from "@/modules/artifacts/types/api";

export function getArtifactDisplayTitle(artifact: ArtifactListItem): string {
  const taskTitle = getTaskDisplayTitle(artifact.task_title);
  if (artifact.name === "dashboard.html") {
    return taskTitle === "New chat" ? "Dashboard" : taskTitle;
  }
  return artifact.name;
}

export function getArtifactKindLabel(name: string): string {
  if (name === "dashboard.html") return "HTML dashboard";
  if (name.endsWith(".md")) return "Markdown";
  return "Document";
}
