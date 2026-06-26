import type { FileArtifact } from "@/modules/task/types/api";

const HIDDEN_CHAT_ARTIFACTS = new Set(["memory.md"]);

export function isChatVisibleArtifact(name: string): boolean {
  return !HIDDEN_CHAT_ARTIFACTS.has(name);
}

export function indexArtifactsById(artifacts: FileArtifact[]): Map<string, FileArtifact> {
  const map = new Map<string, FileArtifact>();
  for (const artifact of artifacts) {
    map.set(artifact.id, artifact);
  }
  return map;
}

export function groupArtifactsByMessage(
  artifacts: Iterable<FileArtifact>,
): Map<string, FileArtifact[]> {
  const map = new Map<string, FileArtifact[]>();
  for (const artifact of artifacts) {
    if (!artifact.message_id || !isChatVisibleArtifact(artifact.name)) continue;
    const list = map.get(artifact.message_id) ?? [];
    list.push(artifact);
    map.set(artifact.message_id, list);
  }
  for (const [messageId, list] of map) {
    map.set(
      messageId,
      [...list].sort((a, b) => a.name.localeCompare(b.name)),
    );
  }
  return map;
}

export function getLatestArtifactByName(
  artifacts: Map<string, FileArtifact>,
  name: string,
): FileArtifact | undefined {
  let latest: FileArtifact | undefined;
  for (const artifact of artifacts.values()) {
    if (artifact.name !== name) continue;
    if (!latest || (artifact.version ?? 0) > (latest.version ?? 0)) {
      latest = artifact;
    }
  }
  return latest;
}

export function resolveMessageArtifacts(
  messageId: string,
  artifactIds: string[] | undefined,
  artifactsByMessage: Map<string, FileArtifact[]>,
  artifactsById: Map<string, FileArtifact>,
): FileArtifact[] {
  const persisted = artifactsByMessage.get(messageId);
  if (persisted?.length) {
    return persisted;
  }
  if (artifactIds?.length) {
    return artifactIds
      .map((id) => artifactsById.get(id))
      .filter((artifact): artifact is FileArtifact => Boolean(artifact))
      .filter((artifact) => isChatVisibleArtifact(artifact.name));
  }
  return [];
}

export function resolveGroupArtifacts(
  messageIds: string[],
  artifactsByMessage: Map<string, FileArtifact[]>,
  artifactsById: Map<string, FileArtifact>,
): FileArtifact[] {
  const latestByName = new Map<string, FileArtifact>();
  for (const messageId of messageIds) {
    for (const artifact of resolveMessageArtifacts(
      messageId,
      undefined,
      artifactsByMessage,
      artifactsById,
    )) {
      const existing = latestByName.get(artifact.name);
      if (!existing || (artifact.version ?? 0) > (existing.version ?? 0)) {
        latestByName.set(artifact.name, artifact);
      }
    }
  }
  return [...latestByName.values()].sort((a, b) => a.name.localeCompare(b.name));
}
