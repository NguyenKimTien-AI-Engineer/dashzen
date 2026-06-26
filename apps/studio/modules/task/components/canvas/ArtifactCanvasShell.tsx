"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { useArtifactCanvasStore } from "@/lib/stores/artifactCanvasStore";
import { Skeleton } from "@/components/ui/skeleton";

const ArtifactCanvasPanel = dynamic(
  () =>
    import("./ArtifactCanvasPanel").then((mod) => mod.ArtifactCanvasPanel),
  {
    loading: () => <Skeleton className="h-full w-full rounded-none" />,
    ssr: false,
  },
);

const MIN_CANVAS_PX = 360;
const MIN_CHAT_PX = 320;
const DEFAULT_CANVAS_RATIO = 0.52;

type ArtifactCanvasShellProps = {
  children: React.ReactNode;
};

function clampCanvasWidth(nextWidth: number, containerWidth: number) {
  const maxCanvas = Math.max(MIN_CANVAS_PX, containerWidth - MIN_CHAT_PX);
  return Math.min(maxCanvas, Math.max(MIN_CANVAS_PX, nextWidth));
}

export function ArtifactCanvasShell({ children }: ArtifactCanvasShellProps) {
  const open = useArtifactCanvasStore((state) => state.open);
  const content = useArtifactCanvasStore((state) => state.content);
  const fullscreen = useArtifactCanvasStore((state) => state.fullscreen);
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasPanelRef = useRef<HTMLDivElement>(null);
  const canvasWidthRef = useRef(0);
  const draggingRef = useRef(false);
  const rafRef = useRef<number | null>(null);
  const pendingWidthRef = useRef<number | null>(null);
  const [canvasWidth, setCanvasWidth] = useState(0);
  const [isResizing, setIsResizing] = useState(false);

  const applyCanvasWidth = useCallback((width: number, resizing = false) => {
    canvasWidthRef.current = width;
    const panel = canvasPanelRef.current;
    if (!panel) return;
    panel.style.width = `${width}px`;
    panel.style.willChange = resizing ? "width" : "";
  }, []);

  useEffect(() => {
    if (!open || !content) {
      setCanvasWidth(0);
      canvasWidthRef.current = 0;
      return;
    }

    const container = containerRef.current;
    if (!container) return;

    const base =
      canvasWidthRef.current > 0
        ? canvasWidthRef.current
        : Math.floor(container.clientWidth * DEFAULT_CANVAS_RATIO);
    setCanvasWidth(clampCanvasWidth(base, container.clientWidth));
  }, [open, content]);

  useLayoutEffect(() => {
    if (!open || !content || canvasWidth <= 0) return;
    applyCanvasWidth(canvasWidth);
  }, [open, content, canvasWidth, applyCanvasWidth]);

  useEffect(() => {
    if (!open || !content) return;

    function onWindowResize() {
      const container = containerRef.current;
      if (!container || draggingRef.current) return;
      const width = clampCanvasWidth(
        canvasWidthRef.current > 0 ? canvasWidthRef.current : MIN_CANVAS_PX,
        container.clientWidth,
      );
      canvasWidthRef.current = width;
      setCanvasWidth(width);
      applyCanvasWidth(width);
    }

    window.addEventListener("resize", onWindowResize);
    return () => window.removeEventListener("resize", onWindowResize);
  }, [open, content, applyCanvasWidth]);

  useEffect(() => {
    return () => {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, []);

  function scheduleWidthUpdate(nextWidth: number) {
    pendingWidthRef.current = nextWidth;
    if (rafRef.current !== null) return;

    rafRef.current = requestAnimationFrame(() => {
      rafRef.current = null;
      if (pendingWidthRef.current === null) return;
      applyCanvasWidth(pendingWidthRef.current, true);
      pendingWidthRef.current = null;
    });
  }

  function handleResizeStart(event: React.PointerEvent<HTMLDivElement>) {
    event.preventDefault();
    draggingRef.current = true;
    setIsResizing(true);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }

  useEffect(() => {
    function onPointerMove(event: PointerEvent) {
      if (!draggingRef.current) return;
      const container = containerRef.current;
      if (!container) return;
      const rect = container.getBoundingClientRect();
      const nextWidth = clampCanvasWidth(rect.right - event.clientX, rect.width);
      scheduleWidthUpdate(nextWidth);
    }

    function stopDragging() {
      if (!draggingRef.current) return;
      draggingRef.current = false;
      setIsResizing(false);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
      if (pendingWidthRef.current !== null) {
        applyCanvasWidth(pendingWidthRef.current, true);
        pendingWidthRef.current = null;
      }
      setCanvasWidth(canvasWidthRef.current);
      applyCanvasWidth(canvasWidthRef.current, false);
    }

    document.addEventListener("pointermove", onPointerMove);
    document.addEventListener("pointerup", stopDragging);
    document.addEventListener("pointercancel", stopDragging);

    return () => {
      document.removeEventListener("pointermove", onPointerMove);
      document.removeEventListener("pointerup", stopDragging);
      document.removeEventListener("pointercancel", stopDragging);
    };
  }, [applyCanvasWidth]);

  if (fullscreen && open && content) {
    return (
      <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden">
        <div className="flex min-h-0 flex-1 flex-col overflow-hidden">{children}</div>
        <ArtifactCanvasPanel />
      </div>
    );
  }

  const showCanvas = open && content && canvasWidth > 0;

  return (
    <div
      ref={containerRef}
      data-resizing={isResizing ? "true" : undefined}
      className="flex h-full min-h-0 w-full flex-1 overflow-hidden"
    >
      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">{children}</div>

      {showCanvas ? (
        <>
          <div className="group relative z-20 w-0 shrink-0">
            <div
              role="separator"
              aria-orientation="vertical"
              aria-label="Resize artifact canvas"
              onPointerDown={handleResizeStart}
              className="absolute bottom-0 left-1/2 top-0 w-4 -translate-x-1/2 cursor-col-resize touch-none"
            />
            <div
              aria-hidden
              className="pointer-events-none absolute bottom-0 left-1/2 top-0 w-px -translate-x-1/2 bg-border/80"
            />
            <div
              aria-hidden
              className={cn(
                "pointer-events-none absolute left-1/2 top-1/2 h-8 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full border bg-background shadow-sm",
                isResizing
                  ? "border-foreground/25 bg-muted"
                  : "border-border/90 group-hover:border-border group-hover:bg-muted/80",
              )}
            />
          </div>
          <div
            ref={canvasPanelRef}
            className="flex h-full min-h-0 shrink-0 flex-col overflow-hidden bg-background contain-layout data-[resizing=true]:[&_iframe]:pointer-events-none data-[resizing=true]:[&_iframe]:opacity-90"
            style={{ width: canvasWidth }}
            data-resizing={isResizing ? "true" : undefined}
          >
            <ArtifactCanvasPanel className="h-full w-full" />
          </div>
        </>
      ) : null}
    </div>
  );
}
