"use client";

import { useState } from "react";
import { ChevronDown, FolderKanban, Pencil, Star, Trash2 } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { useProjects } from "@/modules/project/hooks/useProjects";
import { useTaskTitleActions } from "@/modules/task/hooks/useTaskTitleActions";
import type { Task } from "@/modules/task/types/api";
import { TaskMenuItem } from "./TaskMenuItem";
import { TaskRenameDialog } from "./TaskRenameDialog";
import { TaskDeleteDialog } from "./TaskDeleteDialog";

type TaskTitleMenuProps = {
  taskId: string;
  title: string;
  task?: Task | null;
};

export function TaskTitleMenu({ taskId, title, task }: TaskTitleMenuProps) {
  const { data: projects = [] } = useProjects();
  const [open, setOpen] = useState(false);
  const [projectPickerOpen, setProjectPickerOpen] = useState(false);
  const [renameOpen, setRenameOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [renameValue, setRenameValue] = useState(title);
  const [newProjectName, setNewProjectName] = useState("");

  const {
    busy,
    starred,
    projectId,
    handleToggleStar,
    handleRename,
    handleAssignProject,
    handleCreateProject,
    handleDelete,
  } = useTaskTitleActions(taskId, title, task);

  return (
    <>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <button
            type="button"
            disabled={busy}
            className="flex max-w-full items-center gap-1 text-sm font-medium hover:text-foreground/80"
          >
            <span className="truncate">{title}</span>
            <ChevronDown className="size-4 shrink-0 text-muted-foreground" />
          </button>
        </PopoverTrigger>
        <PopoverContent align="start" side="bottom" className="w-56 p-1">
          <TaskMenuItem
            icon={<Star className={cn("size-4", starred && "fill-current text-amber-500")} />}
            label={starred ? "Unstar" : "Star"}
            onClick={() => {
              setOpen(false);
              void handleToggleStar();
            }}
          />
          <TaskMenuItem
            icon={<Pencil className="size-4" />}
            label="Rename"
            onClick={() => {
              setRenameValue(title);
              setRenameOpen(true);
            }}
          />
          <Popover open={projectPickerOpen} onOpenChange={setProjectPickerOpen}>
            <PopoverTrigger asChild>
              <button
                type="button"
                className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm hover:bg-muted"
              >
                <FolderKanban className="size-4 text-muted-foreground" />
                <span className="flex-1 text-left">Add to project</span>
                <ChevronDown className="size-4 rotate-[-90deg] text-muted-foreground" />
              </button>
            </PopoverTrigger>
            <PopoverContent align="start" side="right" className="w-56 p-1">
              {projectId && (
                <TaskMenuItem
                  icon={<FolderKanban className="size-4" />}
                  label="Remove from project"
                  onClick={() => {
                    setProjectPickerOpen(false);
                    setOpen(false);
                    void handleAssignProject(null);
                  }}
                />
              )}
              {projects.map((project) => (
                <TaskMenuItem
                  key={project.id}
                  icon={<FolderKanban className="size-4" />}
                  label={project.name}
                  onClick={() => {
                    setProjectPickerOpen(false);
                    setOpen(false);
                    void handleAssignProject(project.id);
                  }}
                  className={project.id === projectId ? "bg-muted/60" : undefined}
                />
              ))}
              <div className="my-1 h-px bg-border/50" />
              <div className="space-y-2 px-2 py-1.5">
                <Input
                  placeholder="New project name"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  className="h-8 text-sm"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      void handleCreateProject(newProjectName).then((ok) => {
                        if (ok) {
                          setNewProjectName("");
                          setProjectPickerOpen(false);
                          setOpen(false);
                        }
                      });
                    }
                  }}
                />
                <Button
                  type="button"
                  size="sm"
                  className="w-full"
                  disabled={!newProjectName.trim() || busy}
                  onClick={() => {
                    void handleCreateProject(newProjectName).then((ok) => {
                      if (ok) {
                        setNewProjectName("");
                        setProjectPickerOpen(false);
                        setOpen(false);
                      }
                    });
                  }}
                >
                  Create project
                </Button>
              </div>
            </PopoverContent>
          </Popover>
          <div className="my-1 h-px bg-border/50" />
          <TaskMenuItem
            icon={<Trash2 className="size-4" />}
            label="Delete"
            className="text-destructive hover:bg-destructive/10"
            onClick={() => setDeleteOpen(true)}
          />
        </PopoverContent>
      </Popover>

      <TaskRenameDialog
        open={renameOpen}
        value={renameValue}
        busy={busy}
        onOpenChange={setRenameOpen}
        onChange={setRenameValue}
        onSave={() => {
          void handleRename(renameValue).then((ok) => {
            if (ok) {
              setRenameOpen(false);
              setOpen(false);
            }
          });
        }}
      />

      <TaskDeleteDialog
        open={deleteOpen}
        title={title}
        busy={busy}
        onOpenChange={setDeleteOpen}
        onConfirm={() => {
          void handleDelete().then((ok) => {
            if (ok) setDeleteOpen(false);
          });
        }}
      />
    </>
  );
}
