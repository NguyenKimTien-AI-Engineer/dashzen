"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { ApiError } from "@/lib/api/errors";
import { getTask } from "@/lib/api/tasks";
import { TaskProvider } from "@/modules/task/contexts/task-context";
import { ChatWorkspace } from "@/modules/task/components/chat/ChatWorkspace";

type TaskPageClientProps = {
  taskId: string;
};

function readInitialMessage(taskId: string): string | null {
  if (typeof window === "undefined") return null;
  const stored = sessionStorage.getItem(`task-initial-${taskId}`);
  if (!stored) return null;
  sessionStorage.removeItem(`task-initial-${taskId}`);
  return stored;
}

export function TaskPageClient({ taskId }: TaskPageClientProps) {
  const router = useRouter();
  const [initialMessage] = useState(() => readInitialMessage(taskId));

  useEffect(() => {
    let cancelled = false;

    void getTask(taskId).catch((err) => {
      if (cancelled) return;
      if (err instanceof ApiError && err.status === 404) {
        toast.error("Chat not found");
        router.replace("/app");
        return;
      }
      toast.error("Could not load chat");
      router.replace("/app");
    });

    return () => {
      cancelled = true;
    };
  }, [taskId, router]);

  return (
    <TaskProvider key={taskId} taskId={taskId} initialMessage={initialMessage}>
      <ChatWorkspace taskId={taskId} />
    </TaskProvider>
  );
}
