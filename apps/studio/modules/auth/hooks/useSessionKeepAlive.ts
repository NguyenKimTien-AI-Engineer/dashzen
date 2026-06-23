"use client";

import { useEffect } from "react";

import { refreshSession } from "@/lib/api/client";

const REFRESH_INTERVAL_MS = 10 * 60 * 1000;

/** Proactively refresh access token before the 15-minute JWT expires. */
export function useSessionKeepAlive() {
  useEffect(() => {
    const refresh = () => {
      void refreshSession();
    };

    const interval = window.setInterval(refresh, REFRESH_INTERVAL_MS);

    const onVisible = () => {
      if (document.visibilityState === "visible") {
        refresh();
      }
    };

    document.addEventListener("visibilitychange", onVisible);

    return () => {
      window.clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, []);
}
