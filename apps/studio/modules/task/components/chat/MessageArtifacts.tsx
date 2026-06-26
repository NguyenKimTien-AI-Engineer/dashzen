"use client";

import { ArtifactChatCard } from "@/modules/task/components/canvas/ArtifactChatCard";
import {
  getArtifactKindFromFilename,
  getWorkspaceArtifactTitle,
} from "@/modules/task/lib/artifact-display";
import type { FileArtifact } from "@/modules/task/types/api";

type MessageArtifactsProps = {
  taskId: string;
  artifacts: FileArtifact[];
  dashboardTitle: string;
};

export function MessageArtifacts({ taskId, artifacts, dashboardTitle }: MessageArtifactsProps) {
  if (artifacts.length === 0) return null;

  return (
    <div className="my-3 space-y-2">
      {artifacts.map((artifact) => {
        const kind = getArtifactKindFromFilename(artifact.name);
        const title =
          artifact.name === "dashboard.html"
            ? dashboardTitle
            : getWorkspaceArtifactTitle(artifact.name);
        return (
          <ArtifactChatCard
            key={artifact.id}
            taskId={taskId}
            artifactId={artifact.id}
            title={title}
            content={artifact.content ?? ""}
            filename={artifact.name}
            kind={kind}
            version={artifact.version ?? 1}
          />
        );
      })}
    </div>
  );
}
