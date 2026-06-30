"use client";

import { useState } from "react";
import { ChevronsUpDown, CircleCheck, Clock, FileText } from "lucide-react";
import { cn } from "@/lib/utils";
import { useCyclingLabel } from "@/modules/task/hooks/useCyclingLabel";
import type {
  ActivityLogPayload,
  ActivitySectionPayload,
  ActivityStepPayload,
} from "@/modules/task/types/activity-log";
import { activityLogHasContent, collapseActivitySectionsByTitle } from "@/modules/task/lib/build-live-activity-log";
import { formatUsagePair } from "@/modules/task/lib/format-tokens";
import { MarkdownContent } from "./MarkdownContent";

const TIMELINE_ICON_PX = 20;
const DETAIL_PREVIEW_MAX = 500;
/** Max height per streamed reasoning block (clock icon rows) before scroll. */
const THINK_STEP_MAX_HEIGHT = "max-h-72";
/** Max height of the expanded thinking timeline (all sections). */
const THINKING_PANEL_MAX_HEIGHT = "max-h-[500px]";

function truncate(text: string, max: number): string {
  const trimmed = text.trim();
  if (trimmed.length <= max) return trimmed;
  return `${trimmed.slice(0, max)}…`;
}

function getPreviewMeta(
  log: ActivityLogPayload,
): { text: string; kind: "think" | "tool" } | null {
  for (let i = log.sections.length - 1; i >= 0; i -= 1) {
    const section = log.sections[i];
    const lastStep = section.steps[section.steps.length - 1];
    if (!lastStep) continue;
    if (lastStep.kind === "tool" && lastStep.label) {
      return { text: lastStep.label, kind: "tool" };
    }
    if (lastStep.detail) {
      const line = lastStep.detail.split("\n").find((l) => l.trim())?.trim();
      if (line) {
        return {
          text: line.length > 120 ? `${line.slice(0, 120)}…` : line,
          kind: "think",
        };
      }
    }
  }
  return null;
}

function TimelineStepRow({ step }: { step: ActivityStepPayload }) {
  const iconSlot = (
    <span className="absolute left-0 top-0.5 flex w-5 shrink-0 justify-center bg-background">
      {step.kind === "think" ? (
        <Clock className="size-3.5 text-muted-foreground/70" strokeWidth={2} aria-hidden />
      ) : (
        <FileText className="size-3.5 text-muted-foreground/70" strokeWidth={2} aria-hidden />
      )}
    </span>
  );

  if (step.kind === "think") {
    if (!step.detail.trim()) return null;
    return (
      <div className="relative pl-6">
        {iconSlot}
        <div
          className={cn(
            "min-w-0 text-sm leading-relaxed text-foreground/80",
            THINK_STEP_MAX_HEIGHT,
            "overflow-y-auto overscroll-contain pr-1",
          )}
        >
          <MarkdownContent content={step.detail} />
        </div>
      </div>
    );
  }

  const detail = step.detail ? truncate(step.detail, DETAIL_PREVIEW_MAX) : "";

  return (
    <div className="relative pl-6">
      {iconSlot}
      <div className="min-w-0">
        <p
          className={cn(
            "text-sm",
            step.status === "running" ? "text-muted-foreground/80" : "text-muted-foreground",
          )}
        >
          {step.label}
        </p>
        {detail && step.status !== "running" ? (
          <pre className="mt-1.5 max-h-32 overflow-auto whitespace-pre-wrap break-words font-mono text-xs leading-relaxed text-muted-foreground/80">
            {detail}
          </pre>
        ) : null}
      </div>
    </div>
  );
}

function DoneRow() {
  return (
    <div className="relative pl-6">
      <span className="absolute left-0 top-0.5 flex w-5 shrink-0 justify-center bg-background">
        <CircleCheck className="size-3.5 text-muted-foreground/70" strokeWidth={2} aria-hidden />
      </span>
      <p className="text-sm font-medium text-foreground/70">Done</p>
    </div>
  );
}

function dedupeThinkSteps(steps: ActivityStepPayload[]): ActivityStepPayload[] {
  const seen = new Set<string>();
  return steps.filter((step) => {
    if (step.kind !== "think") return true;
    const detail = step.detail.trim();
    if (!detail) return false;
    const key = detail.slice(0, 240);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function SectionTimeline({
  section,
  isActive = false,
}: {
  section: ActivitySectionPayload;
  isActive?: boolean;
}) {
  const visibleSteps = dedupeThinkSteps(
    section.steps.filter(
      (step) => step.kind === "tool" || step.detail.trim().length > 0,
    ),
  );
  const sectionDone = section.status !== "running" || !isActive;

  if (visibleSteps.length === 0) {
    if (section.status === "running" && isActive) {
      return <p className="pl-6 text-sm text-muted-foreground/70">Working…</p>;
    }
    return null;
  }

  return (
    <div className="space-y-4">
      {section.title !== "Orchestrator" ? (
        <p className="pl-6 text-sm font-medium text-foreground/75">{section.title}</p>
      ) : null}
      {visibleSteps.map((step) => (
        <TimelineStepRow key={step.id} step={step} />
      ))}
      {sectionDone ? <DoneRow /> : null}
      {section.status === "error" ? (
        <p className="pl-6 text-sm text-destructive">Failed</p>
      ) : null}
    </div>
  );
}

type ThinkingPanelProps = {
  activityLog: ActivityLogPayload;
  usage?: { inputTokens: number; outputTokens: number } | null;
  isActive?: boolean;
  /** Controlled collapse for live stream panel */
  collapsed?: boolean;
  onToggle?: () => void;
  /** Uncontrolled default for persisted messages */
  defaultCollapsed?: boolean;
};

export function ThinkingPanel({
  activityLog,
  usage,
  isActive = false,
  collapsed: controlledCollapsed,
  onToggle,
  defaultCollapsed = true,
}: ThinkingPanelProps) {
  const [internalCollapsed, setInternalCollapsed] = useState(defaultCollapsed);
  const collapsed = controlledCollapsed ?? internalCollapsed;
  const cyclingLabel = useCyclingLabel(isActive && !activityLog.header_title);

  if (!activityLogHasContent(activityLog)) {
    return null;
  }

  const headerTitle = (() => {
    const stored = activityLog.header_title.trim();
    if (stored.length >= 3) return stored;
    return isActive ? cyclingLabel : "Thinking";
  })();
  const resolvedUsage =
    usage ??
    (activityLog.usage
      ? {
          inputTokens: activityLog.usage.input_tokens,
          outputTokens: activityLog.usage.output_tokens,
        }
      : null);
  const previewMeta = collapsed ? getPreviewMeta(activityLog) : null;
  const sections = collapseActivitySectionsByTitle(activityLog.sections);

  const handleToggle = () => {
    if (onToggle) {
      onToggle();
    } else {
      setInternalCollapsed((value) => !value);
    }
  };

  return (
    <div className="py-2">
      <button
        type="button"
        onClick={handleToggle}
        className="group flex w-full items-center gap-2 text-left text-sm text-muted-foreground transition-colors hover:text-foreground/80"
        aria-expanded={!collapsed}
      >
        <ChevronsUpDown className="size-4 shrink-0 text-muted-foreground/60" aria-hidden />
        <span
          key={isActive && !activityLog.header_title ? cyclingLabel : headerTitle}
          className="line-clamp-2 flex-1 font-medium text-foreground/75"
        >
          {headerTitle}
        </span>
        {resolvedUsage ? (
          <span
            className="shrink-0 font-mono text-xs tabular-nums text-muted-foreground/70"
            aria-label={`Token usage: ${resolvedUsage.inputTokens} input, ${resolvedUsage.outputTokens} output`}
          >
            {formatUsagePair(resolvedUsage.inputTokens, resolvedUsage.outputTokens)}
          </span>
        ) : null}
      </button>

      {collapsed && previewMeta ? (
        <div className="mt-1.5 flex items-start gap-2 pl-6 text-sm text-muted-foreground/75">
          {previewMeta.kind === "think" ? (
            <Clock className="mt-0.5 size-3.5 shrink-0" strokeWidth={2} aria-hidden />
          ) : (
            <FileText className="mt-0.5 size-3.5 shrink-0" strokeWidth={2} aria-hidden />
          )}
          <div className="line-clamp-3 min-w-0 flex-1 [&_p]:mb-0 [&_p]:leading-relaxed [&_strong]:font-semibold">
            <MarkdownContent
              content={previewMeta.text}
              className="text-sm text-muted-foreground/75"
            />
          </div>
        </div>
      ) : null}

      {!collapsed ? (
        <div
          className={cn(
            "mt-3",
            THINKING_PANEL_MAX_HEIGHT,
            "overflow-y-auto overscroll-contain pr-1",
          )}
        >
          <div className="relative">
            <div
              className="pointer-events-none absolute top-2 bottom-0 w-px -translate-x-1/2 bg-border/80"
              style={{ left: TIMELINE_ICON_PX / 2 }}
              aria-hidden
            />
            <div className="space-y-6">
              {sections.map((section) => (
                <SectionTimeline key={section.id} section={section} isActive={isActive} />
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
