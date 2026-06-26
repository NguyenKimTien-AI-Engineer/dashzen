"use client";

import { useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ArrowUp, Check, MessageCircleQuestion } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { CHAT_COLUMN_CLASS } from "./chat-layout";

// ─── Question parser ────────────────────────────────────────────────────────

type Section = {
  num: number;
  title: string;
  chips: string[];
  isMulti: boolean; // true = checkboxes; false = radio (≤2 options)
};

function extractChips(body: string): string[] {
  // "(Ví dụ: A, B, C)" or "(Ví dụ: A → B → C)"
  const vdMatch = body.match(/\(Ví dụ:\s*([^)]+)\)/i);
  if (vdMatch) {
    const raw = vdMatch[1];
    if (raw.includes("→")) {
      return raw
        .split("→")
        .map((s) => s.trim())
        .filter((s) => s && s !== "v.v." && s !== "...");
    }
    return raw
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s && s !== "v.v." && s !== "..." && s.length < 60);
  }

  // "(A/B/C)" patterns — e.g. "(Ngày/Tháng/Quý)"
  const parenMatches = [...body.matchAll(/\(([^)]{3,60})\)/g)];
  for (const m of parenMatches) {
    const inner = m[1];
    if (inner.includes("/")) {
      return inner.split("/").map((s) => s.trim()).filter(Boolean);
    }
    if (inner.includes(",") && !inner.includes("mock")) {
      const parts = inner.split(",").map((s) => s.trim()).filter(Boolean);
      if (parts.length >= 2) return parts;
    }
  }

  // Binary "A hay B" / "A hoặc B" patterns
  const binaryRe =
    /(?:^|[,;]\s*)([^\n,;?()]+?)\s+(?:hay|hoặc)\s+([^\n,;?()]+?)(?:\s*\?|$)/i;
  const bm = body.match(binaryRe);
  if (bm) {
    const a = bm[1].replace(/^.+(?:tải lên file |sử dụng )/i, "").trim();
    const b = bm[2].replace(/\s*\(mock data\)/i, "").trim() + " (mock)";
    return [a, b].filter(Boolean);
  }

  return [];
}

function parseAgentQuestion(text: string): Section[] {
  const sections: Section[] = [];
  // Split on lines that start a new numbered item
  const rawParts = text.split(/\n(?=\d+\.)/);

  for (const part of rawParts) {
    const headMatch = part.match(/^(\d+)\.\s+\*\*([^*]+)\*\*[:\s]*([\s\S]*)/);
    if (!headMatch) continue;

    const title = headMatch[2].trim();
    const body = headMatch[3].trim();
    const chips = extractChips(body);

    sections.push({
      num: parseInt(headMatch[1], 10),
      title,
      chips,
      isMulti: chips.length > 2,
    });
  }

  return sections;
}

function composeFromSelections(
  sections: Section[],
  selected: Record<number, string[]>,
  extra: string,
): string {
  const lines: string[] = [];
  for (const sec of sections) {
    const picks = selected[sec.num] ?? [];
    if (picks.length > 0) {
      lines.push(`${sec.num}. ${sec.title}: ${picks.join(", ")}`);
    }
  }
  if (extra.trim()) lines.push(extra.trim());
  return lines.join("\n");
}

// ─── Component ──────────────────────────────────────────────────────────────

type ChatAskPromptProps = {
  question: string;
  onAnswer: (answer: string) => void;
  className?: string;
};

export function ChatAskPrompt({ question, onAnswer, className }: ChatAskPromptProps) {
  const sections = useMemo(() => parseAgentQuestion(question), [question]);
  const hasStructuredSections = sections.some((s) => s.chips.length > 0);

  const [selected, setSelected] = useState<Record<number, string[]>>({});
  const [extra, setExtra] = useState("");

  const toggleChip = (sectionNum: number, chip: string, isMulti: boolean) => {
    setSelected((prev) => {
      const current = prev[sectionNum] ?? [];
      if (!isMulti) {
        // Radio — replace selection
        return { ...prev, [sectionNum]: current.includes(chip) ? [] : [chip] };
      }
      // Checkbox — toggle
      const next = current.includes(chip)
        ? current.filter((c) => c !== chip)
        : [...current, chip];
      return { ...prev, [sectionNum]: next };
    });
  };

  const totalSelected = Object.values(selected).reduce((n, arr) => n + arr.length, 0);
  const canSend = totalSelected > 0 || extra.trim().length > 0;

  function handleSend() {
    if (!canSend) return;
    const answer = composeFromSelections(sections, selected, extra);
    onAnswer(answer || extra);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className={cn(CHAT_COLUMN_CLASS, "mb-3 space-y-3", className)}>
      {/* Question card */}
      <div className="rounded-xl border border-border/60 bg-card px-4 py-3 shadow-sm">
        <div className="mb-2 flex items-center gap-2 text-xs font-medium text-muted-foreground">
          <MessageCircleQuestion className="size-3.5 shrink-0" />
          Agent asks
        </div>
        <div className="prose prose-sm max-w-none text-[14px] text-foreground/90 [&_strong]:font-semibold [&_strong]:text-foreground [&_p]:mb-2 [&_p:last-child]:mb-0 [&_ol]:mb-2 [&_ol]:space-y-1.5 [&_ol]:pl-4 [&_li]:leading-relaxed">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{question}</ReactMarkdown>
        </div>
      </div>

      {/* Quick-select panel */}
      {hasStructuredSections && (
        <div className="rounded-xl border border-border/60 bg-card px-4 py-3 shadow-sm space-y-4">
          <p className="text-xs font-medium text-muted-foreground">
            Quick select — click to choose, then send
          </p>

          {sections
            .filter((s) => s.chips.length > 0)
            .map((sec) => {
              const picks = selected[sec.num] ?? [];
              return (
                <div key={sec.num} className="space-y-1.5">
                  <p className="text-xs font-semibold text-foreground/80">{sec.title}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {sec.chips.map((chip) => {
                      const isActive = picks.includes(chip);
                      return (
                        <button
                          key={chip}
                          type="button"
                          onClick={() => toggleChip(sec.num, chip, sec.isMulti)}
                          className={cn(
                            "flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-medium transition-all",
                            isActive
                              ? "border-foreground/30 bg-foreground text-background"
                              : "border-border/60 bg-muted/30 text-foreground/80 hover:border-border hover:bg-muted/60",
                          )}
                        >
                          {isActive && <Check className="size-3 shrink-0" />}
                          {chip}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}

          {/* Extra notes */}
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">
              Additional notes{" "}
              <span className="text-muted-foreground/60">(optional)</span>
            </p>
            <textarea
              value={extra}
              onChange={(e) => setExtra(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Add more details or custom info…"
              rows={2}
              className="w-full resize-none rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-sm outline-none placeholder:text-muted-foreground/50 focus:border-border focus:bg-background"
            />
          </div>

          {/* Send button */}
          <Button
            onClick={handleSend}
            disabled={!canSend}
            size="sm"
            className="w-full gap-2"
          >
            <ArrowUp className="size-3.5" />
            Send answer
            {totalSelected > 0 && (
              <span className="ml-1 rounded-full bg-background/20 px-1.5 py-0.5 text-xs">
                {totalSelected} selected
              </span>
            )}
          </Button>
        </div>
      )}

      {/* Fallback: plain textarea when no chips could be parsed */}
      {!hasStructuredSections && (
        <div className="rounded-xl border border-border/60 bg-card px-4 py-3 shadow-sm space-y-2">
          <textarea
            autoFocus
            value={extra}
            onChange={(e) => setExtra(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your answer…"
            rows={3}
            className="w-full resize-none rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-sm outline-none placeholder:text-muted-foreground/50 focus:border-border focus:bg-background"
          />
          <Button
            onClick={handleSend}
            disabled={!extra.trim()}
            size="sm"
            className="w-full gap-2"
          >
            <ArrowUp className="size-3.5" />
            Send answer
          </Button>
        </div>
      )}
    </div>
  );
}
