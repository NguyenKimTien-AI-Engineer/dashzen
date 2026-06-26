"use client";

import { useCallback, useEffect, useRef } from "react";

const BOTTOM_THRESHOLD = 100;

export function useStreamScroll(deps: unknown[]) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const userScrolledUpRef = useRef(false);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    bottomRef.current?.scrollIntoView({ behavior });
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    function onScroll() {
      const distanceFromBottom =
        container!.scrollHeight - container!.scrollTop - container!.clientHeight;
      userScrolledUpRef.current = distanceFromBottom > BOTTOM_THRESHOLD;
    }

    container.addEventListener("scroll", onScroll, { passive: true });
    return () => container.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (!userScrolledUpRef.current) {
      scrollToBottom("auto");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { containerRef, bottomRef, scrollToBottom };
}
