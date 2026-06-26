import type { Task } from "@/modules/task/types/api";
import type { ChatFilterKey } from "../types";
import { getTaskDisplayTitle } from "./format-relative-time";

export function filterTasks(
  tasks: Task[],
  query: string,
  filter: ChatFilterKey,
): Task[] {
  let list = [...tasks];
  if (filter === "active") {
    list = list.filter((t) => t.status === "active");
  }
  const q = query.trim().toLowerCase();
  if (q) {
    list = list.filter((t) =>
      getTaskDisplayTitle(t.title).toLowerCase().includes(q),
    );
  }
  return list.sort(
    (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
  );
}
