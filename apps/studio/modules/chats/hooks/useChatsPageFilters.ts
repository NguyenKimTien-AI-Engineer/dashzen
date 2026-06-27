"use client";

import { useCallback } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { ChatFilterKey } from "@/modules/chats/types";

function parseFilter(value: string | null): ChatFilterKey {
  return value === "active" ? "active" : "all";
}

export function useChatsPageFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const query = searchParams?.get("q") ?? "";
  const filter = parseFilter(searchParams?.get("filter") ?? null);

  const replaceParams = useCallback(
    (updates: { q?: string; filter?: ChatFilterKey }) => {
      const params = new URLSearchParams(searchParams?.toString() ?? "");

      if (updates.q !== undefined) {
        if (updates.q.trim()) params.set("q", updates.q);
        else params.delete("q");
      }

      if (updates.filter !== undefined) {
        if (updates.filter === "active") params.set("filter", "active");
        else params.delete("filter");
      }

      const qs = params.toString();
      router.replace(qs ? `${pathname ?? "/app/chats"}?${qs}` : (pathname ?? "/app/chats"), { scroll: false });
    },
    [pathname, router, searchParams],
  );

  return {
    query,
    filter,
    setQuery: (q: string) => replaceParams({ q }),
    setFilter: (f: ChatFilterKey) => replaceParams({ filter: f }),
  };
}
