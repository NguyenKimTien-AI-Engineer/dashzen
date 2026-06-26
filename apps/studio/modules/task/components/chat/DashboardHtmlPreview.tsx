"use client";

type DashboardHtmlPreviewProps = {
  html: string;
};

export function DashboardHtmlPreview({ html }: DashboardHtmlPreviewProps) {
  return (
    <div className="my-3 overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-border/20">
      <div className="flex items-center justify-between px-4 py-2">
        <span className="text-sm font-medium">Dashboard preview</span>
        <button
          type="button"
          className="text-xs font-medium text-blue-600 hover:underline"
          onClick={() => {
            const blob = new Blob([html], { type: "text/html;charset=utf-8" });
            const url = URL.createObjectURL(blob);
            window.open(url, "_blank", "noopener,noreferrer");
          }}
        >
          Open in new tab
        </button>
      </div>
      <iframe
        title="Dashboard preview"
        srcDoc={html}
        className="h-[min(70vh,720px)] w-full border-0 bg-white"
        sandbox="allow-scripts allow-same-origin"
      />
    </div>
  );
}
