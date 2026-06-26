"use client";

import Link from "next/link";
import { LayoutDashboard } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatRelativeTime } from "@/modules/chats/lib/format-relative-time";
import {
  getArtifactDisplayTitle,
  getArtifactKindLabel,
} from "@/modules/artifacts/lib/display";
import type { ArtifactListItem } from "@/modules/artifacts/types/api";

type ArtifactCardProps = {
  artifact: ArtifactListItem;
  previewHtml?: string | null;
};

export function ArtifactCard({ artifact, previewHtml }: ArtifactCardProps) {
  const title = getArtifactDisplayTitle(artifact);
  const isDashboard = artifact.name === "dashboard.html";

  return (
    <Link
      href={`/app/artifacts/${artifact.id}`}
      className="group flex flex-col overflow-hidden rounded-xl bg-card shadow-sm ring-1 ring-border/20 transition-shadow hover:shadow-md"
    >
      <div className="relative h-36 overflow-hidden bg-muted/30">
        {isDashboard && previewHtml ? (
          <iframe
            title={`Preview ${title}`}
            srcDoc={previewHtml}
            className="pointer-events-none h-[200%] w-[200%] origin-top-left scale-50 border-0 bg-white"
            sandbox="allow-scripts allow-same-origin"
            tabIndex={-1}
          />
        ) : (
          <div className="flex h-full items-center justify-center text-muted-foreground">
            <LayoutDashboard className="size-10 opacity-40" />
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-card/80 to-transparent" />
      </div>
      <div className="space-y-1 p-4">
        <p className={cn("truncate font-medium text-foreground group-hover:underline")}>
          {title}
        </p>
        <p className="text-sm text-muted-foreground">
          Edited {formatRelativeTime(artifact.edited_at)} · {getArtifactKindLabel(artifact.name)}
        </p>
      </div>
    </Link>
  );
}
