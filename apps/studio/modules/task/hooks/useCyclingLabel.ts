"use client";

import { useEffect, useState } from "react";

const CYCLE_WORDS = ["Through", "thinking", "processing"] as const;
const CYCLE_INTERVAL_MS = 1400;

export function useCyclingLabel(active: boolean): string {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (!active) {
      setIndex(0);
      return;
    }

    const id = window.setInterval(() => {
      setIndex((current) => (current + 1) % CYCLE_WORDS.length);
    }, CYCLE_INTERVAL_MS);

    return () => window.clearInterval(id);
  }, [active]);

  return CYCLE_WORDS[active ? index : 0];
}
