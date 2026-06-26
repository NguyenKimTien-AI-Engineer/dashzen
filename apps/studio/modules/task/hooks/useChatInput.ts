"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { ChatUploadItem } from "@/modules/task/components/chat/ChatUploadPreview";

export type ChatInputVariant = "home" | "chat";

export type UseChatInputOptions = {
  variant?: ChatInputVariant;
  defaultValue?: string;
  autoFocus?: boolean;
  isStreaming?: boolean;
  disabled?: boolean;
  onSend: (text: string) => void;
  onFilesSelected?: (files: File[]) => void;
  externalDraft?: string;
  externalDraftVersion?: number;
};

let uploadIdCounter = 0;
function nextUploadId() {
  uploadIdCounter += 1;
  return `upload-${uploadIdCounter}`;
}

export function useChatInput({
  variant = "chat",
  defaultValue = "",
  autoFocus = false,
  isStreaming = false,
  disabled = false,
  onSend,
  onFilesSelected,
  externalDraft,
  externalDraftVersion,
}: UseChatInputOptions) {
  const [text, setText] = useState(defaultValue);
  const [uploads, setUploads] = useState<ChatUploadItem[]>([]);
  const [isMultiline, setIsMultiline] = useState(false);
  const [needsScroll, setNeedsScroll] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isHome = variant === "home";
  const compactThreshold = isHome ? 72 : 64;

  const resizeTextarea = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;

    const maxHeight = variant === "home" ? 320 : 240;
    el.style.height = "auto";
    const nextHeight = Math.min(el.scrollHeight, maxHeight);
    const shouldExpand = text.includes("\n") || nextHeight > compactThreshold;

    if (!shouldExpand) {
      el.style.height = "";
      setIsMultiline(false);
      setNeedsScroll(false);
      return;
    }

    el.style.height = `${nextHeight}px`;
    setIsMultiline(true);
    setNeedsScroll(el.scrollHeight > maxHeight);
  }, [text, variant, compactThreshold]);

  useEffect(() => {
    if (autoFocus) textareaRef.current?.focus();
  }, [autoFocus]);

  useEffect(() => {
    if (!isStreaming && !disabled) textareaRef.current?.focus();
  }, [isStreaming, disabled]);

  useEffect(() => {
    resizeTextarea();
  }, [text, variant, resizeTextarea]);

  useEffect(() => {
    if (externalDraftVersion === undefined || externalDraft === undefined) return;
    if (externalDraftVersion === 0) return;
    setText(externalDraft);
    requestAnimationFrame(() => {
      resizeTextarea();
      textareaRef.current?.focus();
      const nextPos = externalDraft.length;
      textareaRef.current?.setSelectionRange(nextPos, nextPos);
    });
    // Only sync when the parent bumps draftVersion — not when resizeTextarea changes on each keystroke.
  }, [externalDraft, externalDraftVersion]);

  useEffect(() => {
    return () => {
      uploads.forEach((upload) => {
        if (upload.previewUrl) URL.revokeObjectURL(upload.previewUrl);
      });
    };
  }, [uploads]);

  const handleSend = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed || isStreaming || disabled) return;
    onSend(trimmed);
    setText("");
    setIsMultiline(false);
    setNeedsScroll(false);
    const el = textareaRef.current;
    if (el) el.style.height = "";
  }, [text, isStreaming, disabled, onSend]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  const handleLocalFilesSelected = useCallback(
    (files: File[]) => {
      if (files.length === 0) return;
      const nextUploads: ChatUploadItem[] = files.map((file) => ({
        id: nextUploadId(),
        file,
        previewUrl: file.type.startsWith("image/") ? URL.createObjectURL(file) : null,
      }));
      setUploads((prev) => [...prev, ...nextUploads]);
      onFilesSelected?.(files);
    },
    [onFilesSelected],
  );

  const removeUpload = useCallback((id: string) => {
    setUploads((prev) => {
      const target = prev.find((u) => u.id === id);
      if (target?.previewUrl) URL.revokeObjectURL(target.previewUrl);
      return prev.filter((u) => u.id !== id);
    });
  }, []);

  const handlePaste = useCallback(
    (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
      const items = Array.from(e.clipboardData.items);
      const imageFiles: File[] = [];
      for (const item of items) {
        if (!item.type.startsWith("image/")) continue;
        const blob = item.getAsFile();
        if (!blob) continue;
        const ext = item.type.split("/")[1]?.replace("jpeg", "jpg") ?? "png";
        const name = blob.name && blob.name !== "image.png" ? blob.name : `pasted-image.${ext}`;
        imageFiles.push(new File([blob], name, { type: item.type }));
      }
      if (imageFiles.length > 0) {
        e.preventDefault();
        handleLocalFilesSelected(imageFiles);
        return;
      }
      requestAnimationFrame(resizeTextarea);
    },
    [handleLocalFilesSelected, resizeTextarea],
  );

  const canSend = text.trim().length > 0 && !isStreaming && !disabled;
  const hasUploads = uploads.length > 0;
  const hasText = text.length > 0;
  const useTallEmptyLayout = !hasUploads && !hasText;
  const useExpandedLayout = hasUploads || isMultiline;

  return {
    text,
    setText,
    uploads,
    isMultiline,
    textareaRef,
    fileInputRef,
    isHome,
    canSend,
    hasUploads,
    useTallEmptyLayout,
    useExpandedLayout,
    needsScroll,
    handleSend,
    handleKeyDown,
    handlePaste,
    handleLocalFilesSelected,
    removeUpload,
    resizeTextarea,
  };
}
