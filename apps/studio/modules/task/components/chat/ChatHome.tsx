"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { createProject } from "@/lib/api/projects";
import { createTask, updateTask } from "@/lib/api/tasks";
import { useMe } from "@/modules/auth/hooks/useMe";
import { useProjects } from "@/modules/project/hooks/useProjects";
import { projectKeys } from "@/modules/project/lib/query-keys";
import { ChatInput } from "./ChatInput";

const QUICK_PROMPTS = [
  { label: "Dashboard doanh thu", text: "Tạo dashboard doanh thu theo khu vực với biểu đồ cột" },
  { label: "Dashboard marketing", text: "Tạo dashboard marketing với KPI và funnel chart" },
  { label: "Phân tích dữ liệu", text: "Giúp tôi phân tích dữ liệu bán hàng và đề xuất biểu đồ phù hợp" },
];

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export function ChatHome() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: user } = useMe();
  const { data: projects = [] } = useProjects();
  const [creating, setCreating] = useState(false);
  const [prefill, setPrefill] = useState("");
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);

  const displayName =
    user?.display_name?.trim() ||
    user?.email?.split("@")[0] ||
    "there";

  async function handleSend(text: string) {
    if (creating) return;
    setCreating(true);
    try {
      const task = await createTask();
      if (selectedProjectId) {
        await updateTask(task.id, { project_id: selectedProjectId });
      }
      sessionStorage.setItem(`task-initial-${task.id}`, text);
      router.push(`/app/task/${task.id}`);
    } catch {
      toast.error("Could not create a new chat. Please try again.");
      setCreating(false);
    }
  }

  function handleFilesSelected(files: File[]) {
    if (files.length === 0) return;
    toast.success(`Selected ${files.length} file${files.length > 1 ? "s" : ""}.`);
  }

  async function handleCreateProject(name: string) {
    try {
      const project = await createProject(name);
      setSelectedProjectId(project.id);
      await queryClient.invalidateQueries({ queryKey: projectKeys.all });
      toast.success(`Project "${project.name}" created`);
    } catch {
      toast.error("Could not create project");
    }
  }

  function handleMicClick() {
    toast.info("Microphone input will be enabled in a next update.");
  }

  function handleVoiceClick() {
    toast.info("Voice conversation mode is coming soon.");
  }

  return (
    <div className="flex h-full flex-col items-center justify-center bg-[oklch(0.985_0.002_90)] px-4">
      <div className="mb-8 text-center">
        <h1 className="font-serif text-4xl font-normal tracking-tight text-foreground/90 md:text-5xl">
          {getGreeting()}, {displayName}
        </h1>
      </div>

      <ChatInput
        key={prefill || "default"}
        defaultValue={prefill}
        onSend={handleSend}
        disabled={creating}
        placeholder="How can I help you today?"
        autoFocus
        variant="home"
        className="mb-4"
        onFilesSelected={handleFilesSelected}
        projects={projects}
        selectedProjectId={selectedProjectId}
        onSelectProject={setSelectedProjectId}
        onCreateProject={handleCreateProject}
        onMicClick={handleMicClick}
        onVoiceClick={handleVoiceClick}
      />

      <div className="flex max-w-2xl flex-wrap justify-center gap-2">
        {QUICK_PROMPTS.map((prompt) => (
          <button
            key={prompt.label}
            type="button"
            onClick={() => setPrefill(prompt.text)}
            className="rounded-full border bg-card px-4 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            {prompt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
