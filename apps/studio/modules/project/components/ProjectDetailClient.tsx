"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { getProject, listProjectTasks } from "@/lib/api/projects";
import { projectKeys } from "@/modules/project/lib/query-keys";
import {
  formatRelativeTime,
  getTaskDisplayTitle,
} from "@/modules/chats/lib/format-relative-time";

const LIST_COLUMN_CLASS = "mx-auto w-full max-w-4xl px-6";

export function ProjectDetailClient() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const [query, setQuery] = useState("");

  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: projectKeys.detail(projectId),
    queryFn: () => getProject(projectId),
  });

  const { data: tasks, isLoading: tasksLoading, isError } = useQuery({
    queryKey: projectKeys.tasks(projectId),
    queryFn: () => listProjectTasks(projectId),
  });

  const filtered = useMemo(() => {
    const list = [...(tasks ?? [])];
    const q = query.trim().toLowerCase();
    if (!q) return list;
    return list.filter((t) => getTaskDisplayTitle(t.title).toLowerCase().includes(q));
  }, [tasks, query]);

  const isLoading = projectLoading || tasksLoading;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className={cn("shrink-0 pt-8 pb-6", LIST_COLUMN_CLASS)}>
        <Link
          href="/app/projects"
          className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          Projects
        </Link>
        <h1 className="font-serif text-3xl font-normal tracking-tight text-foreground">
          {projectLoading ? "Loading..." : project?.name ?? "Project"}
        </h1>

        <div className="relative mt-6">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search chats in project..."
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
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full rounded-lg" />
              ))}
            </div>
          )}

          {isError && (
            <p className="py-8 text-center text-sm text-muted-foreground">
              Could not load project chats.
            </p>
          )}

          {!isLoading && !isError && filtered.length === 0 && (
            <p className="py-12 text-center text-sm text-muted-foreground">
              {query.trim()
                ? "No chats match your search."
                : "No chats in this project yet. Add chats from the title menu."}
            </p>
          )}

          {!isLoading && !isError && filtered.length > 0 && (
            <ul className="space-y-1">
              {filtered.map((task) => (
                <li key={task.id}>
                  <Link
                    href={`/app/task/${task.id}`}
                    className="-mx-2 flex items-center justify-between gap-4 rounded-lg px-2 py-4 transition-colors hover:bg-muted/40"
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
