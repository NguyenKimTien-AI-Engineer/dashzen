"use client";

import { memo, useState } from "react";
import {
  Check,
  ChevronDown,
  Code2,
  Copy,
  Eye,
  ExternalLink,
  Maximize2,
  Minimize2,
  RefreshCw,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { useArtifactCanvasStore } from "@/lib/stores/artifactCanvasStore";
import { MarkdownContent } from "@/modules/task/components/chat/MarkdownContent";
import { getArtifactCanvasKindLabel } from "@/modules/task/lib/artifact-display";
import {
  copyTextToClipboard,
  downloadTextFile,
  openHtmlInNewTab,
} from "@/modules/task/lib/html-artifact";

type ArtifactCanvasPanelProps = {
  className?: string;
};

export const ArtifactCanvasPanel = memo(function ArtifactCanvasPanel({
  className,
}: ArtifactCanvasPanelProps) {
  const {
    title,
    content,
    filename,
    kind,
    view,
    refreshKey,
    fullscreen,
    setView,
    setFullscreen,
    closeCanvas,
    refresh,
  } = useArtifactCanvasStore();
  const [copyOpen, setCopyOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const kindLabel = getArtifactCanvasKindLabel(kind);
  const isHtml = kind === "html";

  async function handleCopy() {
    try {
      await copyTextToClipboard(content);
      setCopied(true);
      toast.success("Copied to clipboard");
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Could not copy to clipboard");
    }
  }

  function handleDownload() {
    const mime = isHtml ? "text/html;charset=utf-8" : "text/markdown;charset=utf-8";
    downloadTextFile(content, filename, mime);
    setCopyOpen(false);
    toast.success("Download started");
  }

  function handlePublish() {
    setCopyOpen(false);
    toast.info("Publish artifact is coming soon.");
  }

  function handleOpenExternal() {
    if (!isHtml) return;
    openHtmlInNewTab(content);
  }

  return (
    <div
      className={cn(
        "flex h-full min-h-0 flex-col overflow-hidden bg-background",
        fullscreen && "fixed inset-0 z-50",
        className,
      )}
    >
      <header className="flex shrink-0 items-center gap-2 border-b px-3 py-2">
        <div className="flex items-center gap-1">
          <Button
            type="button"
            size="icon-sm"
            variant={view === "preview" ? "secondary" : "ghost"}
            aria-label="Preview"
            onClick={() => setView("preview")}
          >
            <Eye className="size-4" />
          </Button>
          <Button
            type="button"
            size="icon-sm"
            variant={view === "code" ? "secondary" : "ghost"}
            aria-label="View source"
            onClick={() => setView("code")}
          >
            <Code2 className="size-4" />
          </Button>
        </div>

        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{title}</p>
          <p className="text-xs text-muted-foreground">{kindLabel}</p>
        </div>

        <div className="flex items-center gap-1">
          <Popover open={copyOpen} onOpenChange={setCopyOpen}>
            <PopoverTrigger asChild>
              <Button type="button" size="sm" variant="outline" className="h-8 gap-1 px-2.5">
                {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
                Copy
                <ChevronDown className="size-3.5 opacity-60" />
              </Button>
            </PopoverTrigger>
            <PopoverContent align="end" className="w-52 p-1">
              <button
                type="button"
                onClick={() => void handleCopy()}
                className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-sm hover:bg-muted"
              >
                <Copy className="size-4 text-muted-foreground" />
                Copy {kindLabel}
              </button>
              <button
                type="button"
                onClick={handleDownload}
                className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-sm hover:bg-muted"
              >
                Download as {kindLabel}
              </button>
              <button
                type="button"
                onClick={handlePublish}
                className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-sm hover:bg-muted"
              >
                Publish artifact
              </button>
            </PopoverContent>
          </Popover>

          {isHtml ? (
            <Button
              type="button"
              size="icon-sm"
              variant="ghost"
              aria-label="Refresh preview"
              onClick={refresh}
            >
              <RefreshCw className="size-4" />
            </Button>
          ) : null}

          <Button
            type="button"
            size="icon-sm"
            variant="ghost"
            aria-label={fullscreen ? "Exit fullscreen" : "Fullscreen"}
            onClick={() => setFullscreen(!fullscreen)}
          >
            {fullscreen ? <Minimize2 className="size-4" /> : <Maximize2 className="size-4" />}
          </Button>

          {isHtml ? (
            <Button
              type="button"
              size="icon-sm"
              variant="ghost"
              aria-label="Open in new tab"
              onClick={handleOpenExternal}
            >
              <ExternalLink className="size-4" />
            </Button>
          ) : null}

          <Button
            type="button"
            size="icon-sm"
            variant="ghost"
            aria-label="Close canvas"
            onClick={closeCanvas}
          >
            <X className="size-4" />
          </Button>
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-hidden bg-muted/20">
        {view === "preview" ? (
          isHtml ? (
            <iframe
              key={refreshKey}
              title={`${title} preview`}
              srcDoc={content}
              className="h-full w-full border-0 bg-white"
              sandbox="allow-scripts allow-same-origin"
            />
          ) : (
            <div className="h-full overflow-y-auto bg-background px-5 py-4">
              <MarkdownContent content={content} />
            </div>
          )
        ) : (
          <pre className="h-full overflow-auto p-4 text-xs leading-relaxed text-foreground/90">
            <code>{content}</code>
          </pre>
        )}
      </div>
    </div>
  );
});
