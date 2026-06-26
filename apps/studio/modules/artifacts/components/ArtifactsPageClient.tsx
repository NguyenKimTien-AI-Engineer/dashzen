"use client";

import { useMemo, useState } from "react";
import { ChevronDown, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useArtifacts } from "@/modules/artifacts/hooks/useArtifacts";
import { ArtifactCard } from "./ArtifactCard";
import { getArtifactDisplayTitle } from "@/modules/artifacts/lib/display";

const LIST_COLUMN_CLASS = "mx-auto w-full max-w-5xl px-6";

type SortKey = "updated" | "name";

export function ArtifactsPageClient() {
  const { data: artifacts, isLoading, isError, refetch } = useArtifacts();
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortKey>("updated");

  const filtered = useMemo(() => {
    let list = [...(artifacts ?? [])];
    const q = query.trim().toLowerCase();
    if (q) {
      list = list.filter((a) =>
        getArtifactDisplayTitle(a).toLowerCase().includes(q),
      );
    }
    if (sort === "name") {
      list.sort((a, b) =>
        getArtifactDisplayTitle(a).localeCompare(getArtifactDisplayTitle(b)),
      );
    } else {
      list.sort(
        (a, b) => new Date(b.edited_at).getTime() - new Date(a.edited_at).getTime(),
      );
    }
    return list;
  }, [artifacts, query, sort]);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className={cn("shrink-0 pt-8 pb-6", LIST_COLUMN_CLASS)}>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h1 className="font-serif text-3xl font-normal tracking-tight text-foreground">
            Artifacts
          </h1>
          <div className="relative">
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as SortKey)}
              className="h-9 appearance-none rounded-lg border bg-background py-1.5 pr-8 pl-3 text-sm outline-none focus:ring-2 focus:ring-ring/30"
              aria-label="Sort artifacts"
            >
              <option value="updated">Sort by Last updated</option>
              <option value="name">Sort by Name</option>
            </select>
            <ChevronDown className="pointer-events-none absolute top-1/2 right-2 size-4 -translate-y-1/2 text-muted-foreground" />
          </div>
        </div>

        <p className="mt-2 text-sm text-muted-foreground">
          HTML dashboards and outputs created across your chats.
        </p>

        <div className="relative mt-6">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search artifacts..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="h-11 rounded-xl border-muted-foreground/20 bg-background pl-10 shadow-sm"
          />
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className={cn("pb-10", LIST_COLUMN_CLASS)}>
          {isLoading && (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-52 rounded-xl" />
              ))}
            </div>
          )}

          {isError && (
            <p className="py-8 text-center text-sm text-muted-foreground">
              Could not load artifacts.{" "}
              <button type="button" onClick={() => void refetch()} className="underline">
                Retry
              </button>
            </p>
          )}

          {!isLoading && !isError && filtered.length === 0 && (
            <p className="py-12 text-center text-sm text-muted-foreground">
              {query.trim()
                ? "No artifacts match your search."
                : "No artifacts yet. Create a dashboard in chat to see it here."}
            </p>
          )}

          {!isLoading && !isError && filtered.length > 0 && (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {filtered.map((artifact) => (
                <ArtifactCard key={artifact.id} artifact={artifact} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
