"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { getArtifacts } from "@/lib/api/tasks";
import { taskKeys } from "@/modules/task/lib/query-keys";
import { useTaskContext } from "../contexts/task-context";

export function useTaskArtifacts(taskId: string) {
  return useQuery({
    queryKey: taskKeys.artifacts(taskId),
    queryFn: () => getArtifacts(taskId),
  });
}

/** Syncs workspace artifacts from API when not streaming */
export function TaskArtifactsSync({ taskId }: { taskId: string }) {
  const { syncArtifacts, isStreaming } = useTaskContext();
  const { data, isSuccess } = useTaskArtifacts(taskId);

  useEffect(() => {
    if (isSuccess && data && !isStreaming) {
      syncArtifacts(data);
    }
  }, [data, isSuccess, isStreaming, syncArtifacts]);

  return null;
}
