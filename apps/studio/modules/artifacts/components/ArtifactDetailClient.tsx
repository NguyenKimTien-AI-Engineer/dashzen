"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, ExternalLink, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { formatRelativeTime } from "@/modules/chats/lib/format-relative-time";
import { useArtifact } from "@/modules/artifacts/hooks/useArtifacts";
import { getArtifactDisplayTitle, getArtifactKindLabel } from "@/modules/artifacts/lib/display";

const DashboardHtmlPreview = dynamic(
  () =>
    import("@/modules/task/components/chat/DashboardHtmlPreview").then(
      (mod) => mod.DashboardHtmlPreview,
    ),
  {
    loading: () => <Skeleton className="h-[60vh] w-full rounded-xl" />,
    ssr: false,
  },
);

const COLUMN_CLASS = "mx-auto w-full max-w-4xl px-6";

export function ArtifactDetailClient() {
  const params = useParams<{ artifactId: string }>();
  const artifactId = params?.artifactId ?? "";
  const { data: artifact, isLoading, isError } = useArtifact(artifactId);

  if (isLoading) {
    return (
      <div className={cn("py-8", COLUMN_CLASS)}>
        <Skeleton className="mb-6 h-6 w-32" />
        <Skeleton className="mb-4 h-10 w-2/3" />
        <Skeleton className="h-[60vh] w-full rounded-xl" />
      </div>
    );
  }

  if (isError || !artifact) {
    return (
      <div className={cn("py-12 text-center text-sm text-muted-foreground", COLUMN_CLASS)}>
        Artifact not found.
      </div>
    );
  }

  const title = getArtifactDisplayTitle(artifact);
  const html = artifact.content ?? "";

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className={cn("shrink-0 pt-8 pb-4", COLUMN_CLASS)}>
        <Link
          href="/app/artifacts"
          className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          Artifacts
        </Link>

        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <h1 className="font-serif text-3xl font-normal tracking-tight text-foreground">
              {title}
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Edited {formatRelativeTime(artifact.edited_at)} ·{" "}
              {getArtifactKindLabel(artifact.name)}
            </p>
          </div>
          <div className="flex shrink-0 gap-2">
            <Link
              href={`/app/task/${artifact.task_id}`}
              className="inline-flex h-8 items-center gap-2 rounded-lg border border-border bg-background px-3 text-sm font-medium hover:bg-muted"
            >
              <MessageSquare className="size-4" />
              Open chat
            </Link>
            {html && (
              <Button
                type="button"
                size="sm"
                onClick={() => {
                  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
                  const url = URL.createObjectURL(blob);
                  window.open(url, "_blank", "noopener,noreferrer");
                }}
              >
                <ExternalLink className="size-4" />
                Open HTML
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className={cn("pb-10", COLUMN_CLASS)}>
          {artifact.name === "dashboard.html" && html ? (
            <DashboardHtmlPreview html={html} />
          ) : (
            <pre className="overflow-auto rounded-xl bg-muted/30 p-4 text-xs leading-relaxed">
              {html || "No content"}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
