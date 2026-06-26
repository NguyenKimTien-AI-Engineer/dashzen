"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Code2, Download, FileText, History, LayoutDashboard } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import type { ArtifactCanvasKind } from "@/lib/stores/artifactCanvasStore";
import { useArtifactCanvasStore } from "@/lib/stores/artifactCanvasStore";
import { getArtifactVersions, restoreArtifactVersion } from "@/lib/api/tasks";
import { getArtifactSubtitle } from "@/modules/task/lib/artifact-display";
import { downloadTextFile } from "@/modules/task/lib/html-artifact";
import { taskKeys } from "@/modules/task/lib/query-keys";
import type { FileArtifact } from "@/modules/task/types/api";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";

type ArtifactChatCardProps = {
  taskId: string;
  artifactId: string;
  title: string;
  content: string;
  filename: string;
  kind: ArtifactCanvasKind;
  version: number;
  className?: string;
};

export function ArtifactChatCard({
  taskId,
  artifactId,
  title,
  content,
  filename,
  kind,
  version,
  className,
}: ArtifactChatCardProps) {
  const queryClient = useQueryClient();
  const openCanvas = useArtifactCanvasStore((state) => state.openCanvas);
  const isOpen = useArtifactCanvasStore(
    (state) => state.open && state.filename === filename,
  );
  const [restoring, setRestoring] = useState(false);
  const [versions, setVersions] = useState<FileArtifact[]>([]);
  const [historyOpen, setHistoryOpen] = useState(false);
  const Icon = kind === "html" ? LayoutDashboard : FileText;

  function handleOpen() {
    if (!content) return;
    openCanvas({ title, content, filename, kind });
  }

  function handleDownload(event: React.MouseEvent) {
    event.stopPropagation();
    if (!content) return;
    const mime =
      kind === "html" ? "text/html;charset=utf-8" : "text/markdown;charset=utf-8";
    downloadTextFile(content, filename, mime);
  }

  async function loadVersions() {
    try {
      const rows = await getArtifactVersions(taskId, filename);
      setVersions(rows);
    } catch {
      toast.error("Could not load version history");
    }
  }

  async function handleRestore(target: FileArtifact) {
    if (restoring || target.id === artifactId) return;
    setRestoring(true);
    try {
      await restoreArtifactVersion(taskId, target.id);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: taskKeys.artifacts(taskId) }),
        queryClient.invalidateQueries({ queryKey: taskKeys.messages(taskId) }),
      ]);
      toast.success(`Restored ${filename} to version ${target.version ?? 1}`);
      setHistoryOpen(false);
    } catch {
      toast.error("Could not restore version");
    } finally {
      setRestoring(false);
    }
  }

  return (
    <div
      className={cn(
        "flex w-full max-w-md items-center gap-3 rounded-xl bg-card px-3 py-3 text-left shadow-sm ring-1 transition-shadow hover:shadow-md",
        isOpen ? "ring-foreground/25" : "ring-border/20",
        className,
      )}
    >
      <button
        type="button"
        onClick={handleOpen}
        disabled={!content}
        className="flex min-w-0 flex-1 items-center gap-3 text-left disabled:cursor-not-allowed disabled:opacity-60"
      >
        <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-muted/60 text-muted-foreground">
          <Icon className="size-5" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex items-center gap-2">
            <span className="truncate text-sm font-semibold text-foreground">{title}</span>
            {version >= 2 ? (
              <span className="shrink-0 rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                Version {version}
              </span>
            ) : null}
          </span>
          <span className="mt-0.5 flex items-center gap-1 text-xs text-muted-foreground">
            <Code2 className="size-3" />
            {getArtifactSubtitle(kind)}
          </span>
        </span>
      </button>

      {version >= 2 ? (
        <Popover
          open={historyOpen}
          onOpenChange={(open) => {
            setHistoryOpen(open);
            if (open) void loadVersions();
          }}
        >
          <PopoverTrigger asChild>
            <Button
              type="button"
              size="icon-sm"
              variant="ghost"
              className="shrink-0"
              aria-label={`Version history for ${filename}`}
              disabled={restoring}
            >
              <History className="size-4" />
            </Button>
          </PopoverTrigger>
          <PopoverContent align="end" className="w-48 p-1">
            {(versions.length > 0 ? versions : [{ id: artifactId, version } as FileArtifact])
              .slice()
              .sort((a, b) => (b.version ?? 1) - (a.version ?? 1))
              .map((entry) => (
                <button
                  key={entry.id}
                  type="button"
                  disabled={entry.id === artifactId || restoring}
                  onClick={() => void handleRestore(entry)}
                  className={cn(
                    "flex w-full rounded-lg px-2.5 py-2 text-sm hover:bg-muted disabled:cursor-default disabled:opacity-50",
                    entry.id === artifactId && "bg-muted/60",
                  )}
                >
                  Version {entry.version ?? 1}
                  {entry.id === artifactId ? " (current)" : ""}
                </button>
              ))}
          </PopoverContent>
        </Popover>
      ) : null}

      <span
        role="button"
        tabIndex={0}
        onClick={handleDownload}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            handleDownload(event as unknown as React.MouseEvent);
          }
        }}
        className="inline-flex shrink-0 items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        aria-label={`Download ${filename}`}
      >
        <Download className="size-3.5" />
        Download
      </span>
    </div>
  );
}
