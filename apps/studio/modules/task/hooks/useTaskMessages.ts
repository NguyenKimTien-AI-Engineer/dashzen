"use client";

import { useQuery } from "@tanstack/react-query";
import { getMessages } from "@/lib/api/tasks";
import { taskKeys } from "@/modules/task/lib/query-keys";

export function useTaskMessages(taskId: string) {
  return useQuery({
    queryKey: taskKeys.messages(taskId),
    queryFn: () => getMessages(taskId),
    staleTime: 30_000,
  });
}
