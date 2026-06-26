"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronDown, Plus, Search } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { createTask } from "@/lib/api/tasks";
import { useTasks } from "@/modules/task/hooks/useTasks";
import { useChatsPageFilters } from "@/modules/chats/hooks/useChatsPageFilters";
import { filterTasks } from "@/modules/chats/lib/filter-tasks";
import {
  formatRelativeTime,
  getTaskDisplayTitle,
} from "@/modules/chats/lib/format-relative-time";
import type { ChatFilterKey } from "@/modules/chats/types";

const LIST_COLUMN_CLASS = "mx-auto w-full max-w-4xl px-6";

export function ChatsPageClient() {
  const router = useRouter();
  const { data: tasks, isLoading, isError, refetch } = useTasks();
  const { query, filter, setQuery, setFilter } = useChatsPageFilters();
  const [creating, setCreating] = useState(false);

  const filtered = useMemo(
    () => filterTasks(tasks ?? [], query, filter),
    [tasks, query, filter],
  );

  async function handleNewChat() {
    if (creating) return;
    setCreating(true);
    try {
      const task = await createTask();
      router.push(`/app/task/${task.id}`);
    } catch {
      toast.error("Could not create a new chat. Please try again.");
      setCreating(false);
    }
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className={cn("shrink-0 pt-8 pb-6", LIST_COLUMN_CLASS)}>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h1 className="font-serif text-3xl font-normal tracking-tight text-foreground">
            Chats
          </h1>
          <div className="flex items-center gap-2">
            <div className="relative">
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value as ChatFilterKey)}
                className="h-9 appearance-none rounded-lg border bg-background py-1.5 pr-8 pl-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring/30"
                aria-label="Filter chats"
              >
                <option value="all">All</option>
                <option value="active">Active</option>
              </select>
              <ChevronDown className="pointer-events-none absolute top-1/2 right-2 size-4 -translate-y-1/2 text-muted-foreground" />
            </div>
            <Button
              type="button"
              size="lg"
              className="rounded-lg"
              onClick={() => void handleNewChat()}
              disabled={creating}
            >
              <Plus className="size-4" />
              New chat
            </Button>
          </div>
        </div>

        <div className="relative mt-6">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search chats..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="h-11 rounded-xl border-muted-foreground/20 bg-background pl-10 shadow-sm"
          />
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className={cn("pb-10", LIST_COLUMN_CLASS)}>
          {isLoading && (
            <div className="space-y-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="my-3 h-10 w-full rounded-lg" />
              ))}
            </div>
          )}

          {isError && (
            <p className="py-8 text-center text-sm text-muted-foreground">
              Could not load chats.{" "}
              <button
                type="button"
                onClick={() => void refetch()}
                className="underline hover:text-foreground"
              >
                Retry
              </button>
            </p>
          )}

          {!isLoading && !isError && filtered.length === 0 && (
            <p className="py-12 text-center text-sm text-muted-foreground">
              {query.trim() ? "No chats match your search." : "No chats yet. Start a new conversation."}
            </p>
          )}

          {!isLoading && !isError && filtered.length > 0 && (
            <ul className="space-y-1">
              {filtered.map((task) => (
                <li key={task.id}>
                  <Link
                    href={`/app/task/${task.id}`}
                    className="flex items-center justify-between gap-4 py-4 transition-colors hover:bg-muted/40 -mx-2 px-2 rounded-lg"
                  >
                    <span className="min-w-0 truncate text-[15px] text-foreground">
                      {getTaskDisplayTitle(task.title)}
                    </span>
                    <span className="shrink-0 text-sm text-muted-foreground">
                      {formatRelativeTime(task.updated_at)}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
