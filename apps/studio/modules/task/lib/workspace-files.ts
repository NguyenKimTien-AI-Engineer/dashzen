import type { FileArtifact } from "@/modules/task/types/api";
import type { AgentBlockState } from "@/modules/task/types/task-state";

const HIDDEN_ARTIFACTS = new Set(["memory.md", "dashboard.html"]);

const DASHBOARD_ARTIFACTS = new Set([
  "spec.md",
  "bindings.md",
  "layout.md",
  "dashboard.html",
]);

const DASHBOARD_AGENTS = new Set([
  "dashboard-planner",
  "data-binder",
  "layout-designer",
  "dashboard-builder",
]);

export function getVisibleWorkspaceArtifacts(
  artifacts: Map<string, FileArtifact>,
): FileArtifact[] {
  return Array.from(artifacts.values()).filter((a) => !HIDDEN_ARTIFACTS.has(a.name));
}

export function isDashboardWorkspace(
  taskType: string | null | undefined,
  agentBlocks: Map<string, AgentBlockState>,
  artifacts: Map<string, FileArtifact>,
): boolean {
  if (taskType === "dashboard") return true;

  for (const block of agentBlocks.values()) {
    if (DASHBOARD_AGENTS.has(block.name)) return true;
  }

  for (const name of artifacts.keys()) {
    if (DASHBOARD_ARTIFACTS.has(name)) return true;
  }

  return false;
}

export function shouldShowWorkspaceFiles(
  taskType: string | null | undefined,
  agentBlocks: Map<string, AgentBlockState>,
  artifacts: Map<string, FileArtifact>,
): boolean {
  if (!isDashboardWorkspace(taskType, agentBlocks, artifacts)) return false;
  return getVisibleWorkspaceArtifacts(artifacts).length > 0;
}
