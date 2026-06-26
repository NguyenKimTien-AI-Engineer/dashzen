"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { FileSpreadsheet, Loader2, X } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  getDisplayFileName,
  getFilePreviewKind,
  getFileTypeLabel,
} from "@/modules/task/lib/file-upload-preview";
import { renderPdfThumbnail } from "@/modules/task/lib/pdf-thumbnail";

export type ChatUploadItem = {
  id: string;
  file: File;
  previewUrl: string | null;
};

type ChatUploadPreviewProps = {
  upload: ChatUploadItem;
  size?: "home" | "chat";
  onRemove: (id: string) => void;
};

const CARD_CLASS =
  "relative overflow-hidden rounded-xl bg-background ring-1 ring-border/50 shadow-sm";

function FileTypeBadge({ label }: { label: string }) {
  return (
    <span className="absolute bottom-1.5 left-1.5 rounded px-1.5 py-0.5 text-[9px] font-semibold tracking-wide bg-black text-white">
      {label}
    </span>
  );
}

function RemoveButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={`Remove ${label}`}
      className="absolute -top-1.5 -right-1.5 z-10 flex size-5 items-center justify-center rounded-full bg-foreground text-background shadow-sm ring-2 ring-card transition-opacity hover:opacity-90"
    >
      <X className="size-3" strokeWidth={2.5} />
    </button>
  );
}

function DocumentPreviewBody({
  file,
  pdfThumbUrl,
  pdfLoading,
}: {
  file: File;
  pdfThumbUrl: string | null;
  pdfLoading: boolean;
}) {
  const kind = getFilePreviewKind(file);
  const displayName = getDisplayFileName(file.name);

  if (kind === "pdf") {
    if (pdfLoading) {
      return (
        <div className="flex h-full w-full items-center justify-center bg-muted/30">
          <Loader2 className="size-4 animate-spin text-muted-foreground" />
        </div>
      );
    }

    if (pdfThumbUrl) {
      return (
        <Image
          src={pdfThumbUrl}
          alt={file.name}
          fill
          unoptimized
          className="object-cover object-top"
        />
      );
    }
  }

  const Icon = kind === "spreadsheet" ? FileSpreadsheet : null;

  return (
    <div className="flex h-full flex-col justify-between p-3">
      <p className="line-clamp-4 text-[11px] leading-snug font-medium text-foreground/90">
        {displayName}
      </p>
      {Icon ? <Icon className="size-4 shrink-0 text-muted-foreground/70" aria-hidden /> : null}
    </div>
  );
}

export function ChatUploadPreview({ upload, size = "chat", onRemove }: ChatUploadPreviewProps) {
  const { file, previewUrl } = upload;
  const kind = getFilePreviewKind(file);
  const label = getFileTypeLabel(file);
  const isImage = kind === "image" && previewUrl;
  const isHome = size === "home";

  const [pdfThumbUrl, setPdfThumbUrl] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(kind === "pdf");

  useEffect(() => {
    if (kind !== "pdf") return;

    let cancelled = false;
    setPdfLoading(true);

    void (async () => {
      const thumb = await renderPdfThumbnail(file, isHome ? 240 : 208);
      if (cancelled) return;
      setPdfThumbUrl(thumb);
      setPdfLoading(false);
    })();

    return () => {
      cancelled = true;
    };
  }, [file, kind, isHome]);

  if (isImage) {
    return (
      <div className="group relative shrink-0">
        <Image
          src={previewUrl}
          alt={file.name}
          width={isHome ? 112 : 96}
          height={isHome ? 112 : 96}
          unoptimized
          className={cn(
            "rounded-xl object-cover ring-1 ring-border/50 shadow-sm",
            isHome ? "h-28 w-28" : "h-24 w-24",
          )}
        />
        <RemoveButton label={file.name} onClick={() => onRemove(upload.id)} />
      </div>
    );
  }

  return (
    <div className="group relative shrink-0">
      <div
        className={cn(CARD_CLASS, isHome ? "h-28 w-36" : "h-24 w-32")}
        title={file.name}
      >
        <DocumentPreviewBody file={file} pdfThumbUrl={pdfThumbUrl} pdfLoading={pdfLoading} />
        <FileTypeBadge label={label} />
      </div>
      <RemoveButton label={file.name} onClick={() => onRemove(upload.id)} />
    </div>
  );
}
