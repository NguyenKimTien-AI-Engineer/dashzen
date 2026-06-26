"use client";

import { useState } from "react";
import { ChevronRight, FolderPlus, Paperclip, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import type { Project } from "@/modules/project/types/api";

type ChatInputActionsMenuProps = {
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  projects?: Project[];
  selectedProjectId?: string | null;
  onSelectProject?: (projectId: string | null) => void;
  onCreateProject?: (name: string) => Promise<void> | void;
};

export function ChatInputActionsMenu({
  fileInputRef,
  projects = [],
  selectedProjectId = null,
  onSelectProject,
  onCreateProject,
}: ChatInputActionsMenuProps) {
  const [actionsOpen, setActionsOpen] = useState(false);
  const [projectsOpen, setProjectsOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [creatingProject, setCreatingProject] = useState(false);

  const hasProjectActions = Boolean(onSelectProject || onCreateProject);

  async function handleCreateProject() {
    const trimmed = newProjectName.trim();
    if (!trimmed || !onCreateProject || creatingProject) return;
    try {
      setCreatingProject(true);
      await onCreateProject(trimmed);
      setNewProjectName("");
    } finally {
      setCreatingProject(false);
    }
  }

  return (
    <Popover open={actionsOpen} onOpenChange={setActionsOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          size="icon-sm"
          variant="ghost"
          className="rounded-md text-muted-foreground"
          aria-label="More actions"
        >
          <Plus className="size-4" />
        </Button>
      </PopoverTrigger>
      <PopoverContent side="top" align="start" className="w-72 p-1.5">
        <button
          type="button"
          onClick={() => {
            setActionsOpen(false);
            fileInputRef.current?.click();
          }}
          className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm hover:bg-muted"
        >
          <Paperclip className="size-4 text-muted-foreground" />
          <span className="flex-1 text-left">Add files or photos</span>
          <span className="text-xs text-muted-foreground">Ctrl+U</span>
        </button>
        {hasProjectActions && (
          <>
            <Popover open={projectsOpen} onOpenChange={setProjectsOpen}>
              <PopoverTrigger asChild>
                <button
                  type="button"
                  className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm hover:bg-muted"
                >
                  <FolderPlus className="size-4 text-muted-foreground" />
                  <span className="flex-1 text-left">Add to project</span>
                  <ChevronRight className="size-4 text-muted-foreground" />
                </button>
              </PopoverTrigger>
              <PopoverContent side="right" align="start" className="w-80 p-1.5">
                <div className="max-h-56 overflow-auto pr-1">
                  {projects.length === 0 && (
                    <p className="px-2 py-2 text-sm text-muted-foreground">No projects yet</p>
                  )}
                  {projects.map((project) => (
                    <button
                      key={project.id}
                      type="button"
                      onClick={() => {
                        onSelectProject?.(project.id);
                        setProjectsOpen(false);
                        setActionsOpen(false);
                      }}
                      className={cn(
                        "flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm hover:bg-muted",
                        selectedProjectId === project.id && "bg-muted/70",
                      )}
                    >
                      <FolderPlus className="size-4 text-muted-foreground" />
                      <span className="flex-1 text-left">{project.name}</span>
                    </button>
                  ))}
                </div>
                {onCreateProject && (
                  <>
                    <div className="my-1 h-px bg-border/60" />
                    <div className="space-y-2 px-1 py-1">
                      <Input
                        value={newProjectName}
                        onChange={(e) => setNewProjectName(e.target.value)}
                        placeholder="Start a new project"
                        className="h-8 text-sm"
                        onKeyDown={(e) => {
                          if (e.key === "Enter") void handleCreateProject();
                        }}
                      />
                      <Button
                        type="button"
                        size="sm"
                        className="w-full"
                        disabled={!newProjectName.trim() || creatingProject}
                        onClick={() => void handleCreateProject()}
                      >
                        Start a new project
                      </Button>
                    </div>
                  </>
                )}
              </PopoverContent>
            </Popover>
            {selectedProjectId && (
              <>
                <div className="my-1 h-px bg-border/60" />
                <button
                  type="button"
                  onClick={() => {
                    onSelectProject?.(null);
                    setActionsOpen(false);
                  }}
                  className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm hover:bg-muted"
                >
                  <FolderPlus className="size-4 text-muted-foreground" />
                  <span className="flex-1 text-left">Remove from project</span>
                </button>
              </>
            )}
          </>
        )}
      </PopoverContent>
    </Popover>
  );
}
