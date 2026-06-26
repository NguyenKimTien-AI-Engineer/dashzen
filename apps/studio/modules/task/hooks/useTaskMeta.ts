"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { getTask } from "@/lib/api/tasks";
import { taskKeys } from "@/modules/task/lib/query-keys";
import { useTaskContext } from "../contexts/task-context";

export function useTaskDetail(taskId: string) {
  return useQuery({
    queryKey: taskKeys.detail(taskId),
    queryFn: () => getTask(taskId),
  });
}

/** Syncs task title/type from API when not streaming */
export function TaskMetaSync({ taskId }: { taskId: string }) {
  const { syncTaskMeta, isStreaming } = useTaskContext();
  const { data, isSuccess } = useTaskDetail(taskId);

  useEffect(() => {
    if (isSuccess && data && !isStreaming) {
      syncTaskMeta({
        title: data.title ?? undefined,
        taskType: data.type ?? undefined,
      });
    }
  }, [data, isSuccess, isStreaming, syncTaskMeta]);

  return null;
}
