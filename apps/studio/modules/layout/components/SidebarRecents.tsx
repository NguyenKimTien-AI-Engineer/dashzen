"use client";

import { usePathname } from "next/navigation";
import { Star } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { useTasks } from "@/modules/task/hooks/useTasks";
import { Skeleton } from "@/components/ui/skeleton";

const MAX_RECENTS = 15;

type SidebarRecentsProps = {
  collapsed: boolean;
};

function getTaskTitle(title: string | null): string {
  return title?.trim() || "New chat";
}

type TaskLinkProps = {
  id: string;
  title: string | null;
  isActive: boolean;
};

function TaskLink({ id, title, isActive }: TaskLinkProps) {
  return (
    <Link
      href={`/app/task/${id}`}
      className={cn(
        "block rounded-lg px-3 py-2 text-sm transition-colors",
        isActive
          ? "bg-muted font-medium text-foreground"
          : "text-foreground/75 hover:bg-muted/60 hover:text-foreground",
      )}
    >
      <span className="line-clamp-1">{getTaskTitle(title)}</span>
    </Link>
  );
}

export function SidebarRecents({ collapsed }: SidebarRecentsProps) {
  const pathname = usePathname();
  const { data: tasks, isLoading, isError, refetch } = useTasks();

  if (collapsed) return null;

  const sorted = [...(tasks ?? [])].sort(
    (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
  );

  const starredTasks = sorted.filter((t) => t.starred);
  const recentTasks = sorted.filter((t) => !t.starred).slice(0, MAX_RECENTS);

  return (
    <div className="mt-2 flex min-h-0 flex-1 flex-col gap-4 px-2 pb-4">
      {/* ── Starred ─────────────────────────────────────────────── */}
      {(isLoading || starredTasks.length > 0) && (
        <div className="flex flex-col gap-0.5">
          <div className="mb-1 flex items-center gap-1.5 px-3">
            <Star className="size-3 fill-amber-400 text-amber-400" />
            <span className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
              Starred
            </span>
          </div>

          {isLoading &&
            Array.from({ length: 2 }).map((_, i) => (
              <Skeleton key={i} className="mx-1 h-8 rounded-lg" />
            ))}

          {!isLoading && starredTasks.length === 0 && (
            <p className="px-3 py-1 text-xs text-muted-foreground">No starred chats</p>
          )}

          {starredTasks.map((task) => (
            <TaskLink
              key={task.id}
              id={task.id}
              title={task.title}
              isActive={pathname === `/app/task/${task.id}`}
            />
          ))}
        </div>
      )}

      {/* ── Recents ─────────────────────────────────────────────── */}
      <div className="flex min-h-0 flex-1 flex-col gap-0.5">
        <div className="mb-1 px-3">
          <span className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
            Recents
          </span>
        </div>

        {isLoading &&
          Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="mx-1 h-8 rounded-lg" />
          ))}

        {isError && (
          <div className="px-3 py-2 text-xs text-muted-foreground">
            Could not load chats.{" "}
            <button
              type="button"
              onClick={() => void refetch()}
              className="underline hover:text-foreground"
            >
              Retry
            </button>
          </div>
        )}

        {!isLoading && !isError && recentTasks.length === 0 && (
          <p className="px-3 py-1 text-xs text-muted-foreground">No chats yet</p>
        )}

        <div className="overflow-y-auto">
          {recentTasks.map((task) => (
            <TaskLink
              key={task.id}
              id={task.id}
              title={task.title}
              isActive={pathname === `/app/task/${task.id}`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
