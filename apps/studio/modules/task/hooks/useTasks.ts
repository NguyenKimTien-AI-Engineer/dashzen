import { useQuery } from "@tanstack/react-query";
import { listTasks } from "@/lib/api/tasks";
import { taskKeys } from "@/modules/task/lib/query-keys";

export function useTasks() {
  return useQuery({
    queryKey: taskKeys.all,
    queryFn: () => listTasks(),
  });
}
