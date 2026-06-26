"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { createProject } from "@/lib/api/projects";
import { deleteTask, updateTask } from "@/lib/api/tasks";
import { projectKeys } from "@/modules/project/lib/query-keys";
import { taskKeys } from "@/modules/task/lib/query-keys";
import type { Task } from "@/modules/task/types/api";

export function useTaskTitleActions(taskId: string, title: string, task?: Task | null) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [busy, setBusy] = useState(false);

  const starred = task?.starred ?? false;
  const projectId = task?.project_id ?? null;

  async function invalidate() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: taskKeys.detail(taskId) }),
      queryClient.invalidateQueries({ queryKey: taskKeys.all }),
      queryClient.invalidateQueries({ queryKey: projectKeys.all }),
    ]);
  }

  async function handleToggleStar() {
    setBusy(true);
    try {
      await updateTask(taskId, { starred: !starred });
      await invalidate();
      toast.success(starred ? "Removed from starred" : "Added to starred");
    } catch {
      toast.error("Could not update chat");
    } finally {
      setBusy(false);
    }
  }

  async function handleRename(renameValue: string) {
    const trimmed = renameValue.trim();
    if (!trimmed) return false;
    setBusy(true);
    try {
      await updateTask(taskId, { title: trimmed });
      await invalidate();
      toast.success("Chat renamed");
      return true;
    } catch {
      toast.error("Could not rename chat");
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function handleAssignProject(targetProjectId: string | null) {
    setBusy(true);
    try {
      await updateTask(taskId, { project_id: targetProjectId });
      await invalidate();
      toast.success(targetProjectId ? "Added to project" : "Removed from project");
    } catch {
      toast.error("Could not update project");
    } finally {
      setBusy(false);
    }
  }

  async function handleCreateProject(name: string) {
    const trimmed = name.trim();
    if (!trimmed) return false;
    setBusy(true);
    try {
      const project = await createProject(trimmed);
      await updateTask(taskId, { project_id: project.id });
      await invalidate();
      toast.success(`Added to "${project.name}"`);
      return true;
    } catch {
      toast.error("Could not create project");
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    setBusy(true);
    try {
      await deleteTask(taskId);
      await queryClient.invalidateQueries({ queryKey: taskKeys.all });
      toast.success("Chat deleted");
      router.push("/app");
      return true;
    } catch {
      toast.error("Could not delete chat");
      return false;
    } finally {
      setBusy(false);
    }
  }

  return {
    busy,
    starred,
    projectId,
    handleToggleStar,
    handleRename,
    handleAssignProject,
    handleCreateProject,
    handleDelete,
  };
}
