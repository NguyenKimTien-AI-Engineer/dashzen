"use client";

import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";
import { normalizeMarkdownContent } from "@/modules/task/lib/normalize-markdown";

const markdownComponents: Components = {
  h1: ({ children }) => (
    <h1 className="mt-6 mb-3 text-xl font-semibold tracking-tight first:mt-0">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="mt-5 mb-2.5 text-lg font-semibold tracking-tight first:mt-0">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="mt-4 mb-2 text-base font-semibold first:mt-0">{children}</h3>
  ),
  h4: ({ children }) => (
    <h4 className="mt-3 mb-1.5 text-[15px] font-semibold first:mt-0">{children}</h4>
  ),
  p: ({ children }) => <p className="mb-3 leading-7 last:mb-0">{children}</p>,
  ul: ({ children }) => (
    <ul className="mb-3 space-y-1.5 pl-5 [list-style-type:disc] marker:text-foreground/45">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="mb-3 space-y-1.5 pl-5 [list-style-type:decimal] marker:text-foreground/45">
      {children}
    </ol>
  ),
  li: ({ children }) => <li className="leading-7 pl-0.5">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
  em: ({ children }) => <em className="italic text-foreground/90">{children}</em>,
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="font-medium text-foreground underline decoration-foreground/30 underline-offset-2 hover:decoration-foreground/60"
    >
      {children}
    </a>
  ),
  blockquote: ({ children }) => (
    <blockquote className="my-3 border-l-2 border-foreground/15 pl-4 text-muted-foreground italic">
      {children}
    </blockquote>
  ),
  hr: () => <hr className="my-5 border-0 border-t border-border/50" />,
  table: ({ children }) => (
    <div className="my-4 overflow-x-auto rounded-xl bg-muted/25 ring-1 ring-border/30">
      <table className="w-full min-w-[280px] border-collapse text-sm">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-muted/40">{children}</thead>,
  tbody: ({ children }) => <tbody className="divide-y divide-border/40">{children}</tbody>,
  tr: ({ children }) => <tr className="transition-colors hover:bg-muted/20">{children}</tr>,
  th: ({ children }) => (
    <th className="px-3 py-2.5 text-left text-xs font-semibold tracking-wide text-foreground/80 uppercase">
      {children}
    </th>
  ),
  td: ({ children }) => <td className="px-3 py-2.5 align-top leading-relaxed">{children}</td>,
  pre: ({ children }) => (
    <pre className="my-3 overflow-x-auto rounded-xl bg-muted/50 p-4 text-[13px] leading-relaxed">
      {children}
    </pre>
  ),
  code: ({ className, children, ...props }) => {
    const isBlock = Boolean(className?.includes("language-"));
    if (isBlock) {
      return (
        <code className={cn("font-mono text-[13px]", className)} {...props}>
          {children}
        </code>
      );
    }
    return (
      <code
        className="rounded-md bg-muted/70 px-1.5 py-0.5 font-mono text-[0.9em] text-foreground"
        {...props}
      >
        {children}
      </code>
    );
  },
};

type MarkdownContentProps = {
  content: string;
  className?: string;
  streaming?: boolean;
};

export function MarkdownContent({ content, className, streaming: _streaming }: MarkdownContentProps) {
  const normalized = normalizeMarkdownContent(content);

  return (
    <div className={cn("text-[15px] text-foreground/90", className)}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
        {normalized}
      </ReactMarkdown>
    </div>
  );
}
