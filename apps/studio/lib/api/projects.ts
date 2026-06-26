import { fetchWithAuth } from "./client";
import type { Project } from "@/modules/project/types/api";
import type { Task } from "@/modules/task/types/api";

export async function createProject(name: string): Promise<Project> {
  const res = await fetchWithAuth("/v1/projects", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  return res.json() as Promise<Project>;
}

export async function listProjects(): Promise<Project[]> {
  const res = await fetchWithAuth("/v1/projects");
  return res.json() as Promise<Project[]>;
}

export async function getProject(id: string): Promise<Project> {
  const res = await fetchWithAuth(`/v1/projects/${id}`);
  return res.json() as Promise<Project>;
}

export async function updateProject(id: string, name: string): Promise<Project> {
  const res = await fetchWithAuth(`/v1/projects/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ name }),
  });
  return res.json() as Promise<Project>;
}

export async function deleteProject(id: string): Promise<void> {
  await fetchWithAuth(`/v1/projects/${id}`, { method: "DELETE" });
}

export async function listProjectTasks(projectId: string): Promise<Task[]> {
  const res = await fetchWithAuth(`/v1/projects/${projectId}/tasks`);
  return res.json() as Promise<Task[]>;
}
