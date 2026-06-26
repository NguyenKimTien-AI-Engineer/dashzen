"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronDown, FolderKanban, Plus, Search } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { createProject } from "@/lib/api/projects";
import { useProjects } from "@/modules/project/hooks/useProjects";
import { formatRelativeTime } from "@/modules/chats/lib/format-relative-time";

const LIST_COLUMN_CLASS = "mx-auto w-full max-w-5xl px-6";

type SortKey = "updated" | "name";

export function ProjectsPageClient() {
  const router = useRouter();
  const { data: projects, isLoading, isError, refetch } = useProjects();
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortKey>("updated");
  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);

  const filtered = useMemo(() => {
    let list = [...(projects ?? [])];
    const q = query.trim().toLowerCase();
    if (q) {
      list = list.filter((p) => p.name.toLowerCase().includes(q));
    }
    if (sort === "name") {
      list.sort((a, b) => a.name.localeCompare(b.name));
    } else {
      list.sort(
        (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
      );
    }
    return list;
  }, [projects, query, sort]);

  async function handleCreate() {
    const trimmed = newName.trim();
    if (!trimmed || creating) return;
    setCreating(true);
    try {
      const project = await createProject(trimmed);
      setCreateOpen(false);
      setNewName("");
      router.push(`/app/projects/${project.id}`);
    } catch {
      toast.error("Could not create project");
      setCreating(false);
    }
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className={cn("shrink-0 pt-8 pb-6", LIST_COLUMN_CLASS)}>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h1 className="font-serif text-3xl font-normal tracking-tight text-foreground">
            Projects
          </h1>
          <div className="flex items-center gap-2">
            <div className="relative">
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value as SortKey)}
                className="h-9 appearance-none rounded-lg border bg-background py-1.5 pr-8 pl-3 text-sm outline-none focus:ring-2 focus:ring-ring/30"
                aria-label="Sort projects"
              >
                <option value="updated">Sort by Last updated</option>
                <option value="name">Sort by Name</option>
              </select>
              <ChevronDown className="pointer-events-none absolute top-1/2 right-2 size-4 -translate-y-1/2 text-muted-foreground" />
            </div>
            <Button
              type="button"
              size="lg"
              className="rounded-lg"
              onClick={() => setCreateOpen(true)}
            >
              <Plus className="size-4" />
              New project
            </Button>
          </div>
        </div>

        <div className="relative mt-6">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search projects..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="h-11 rounded-xl border-muted-foreground/20 bg-background pl-10 shadow-sm"
          />
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className={cn("pb-10", LIST_COLUMN_CLASS)}>
          {isLoading && (
            <div className="grid gap-4 sm:grid-cols-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-28 rounded-xl" />
              ))}
            </div>
          )}

          {isError && (
            <p className="py-8 text-center text-sm text-muted-foreground">
              Could not load projects.{" "}
              <button type="button" onClick={() => void refetch()} className="underline">
                Retry
              </button>
            </p>
          )}

          {!isLoading && !isError && filtered.length === 0 && (
            <p className="py-12 text-center text-sm text-muted-foreground">
              {query.trim()
                ? "No projects match your search."
                : "No projects yet. Create one to organize your chats."}
            </p>
          )}

          {!isLoading && !isError && filtered.length > 0 && (
            <div className="grid gap-4 sm:grid-cols-2">
              {filtered.map((project) => (
                <Link
                  key={project.id}
                  href={`/app/projects/${project.id}`}
                  className="group rounded-xl bg-card p-5 shadow-sm ring-1 ring-border/20 transition-shadow hover:shadow-md"
                >
                  <div className="flex items-start gap-3">
                    <FolderKanban className="mt-0.5 size-5 shrink-0 text-muted-foreground" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium text-foreground group-hover:underline">
                        {project.name}
                      </p>
                      <p className="mt-3 text-sm text-muted-foreground">
                        Updated {formatRelativeTime(project.updated_at)}
                        {project.task_count > 0 && ` · ${project.task_count} chats`}
                      </p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New project</DialogTitle>
          </DialogHeader>
          <Input
            placeholder="Project name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") void handleCreate();
            }}
            autoFocus
          />
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button
              type="button"
              onClick={() => void handleCreate()}
              disabled={!newName.trim() || creating}
            >
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
