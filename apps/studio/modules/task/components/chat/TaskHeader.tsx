"use client";

import { useQuery } from "@tanstack/react-query";
import { getTask } from "@/lib/api/tasks";
import { taskKeys } from "@/modules/task/lib/query-keys";
import { useTask } from "@/modules/task/hooks/useTask";
import { CHAT_HEADER_CLASS } from "./chat-layout";
import { TaskTitleMenu } from "./TaskTitleMenu";
import { getTaskDisplayTitle } from "@/modules/chats/lib/format-relative-time";

type TaskHeaderProps = {
  taskId: string;
};

export function TaskHeader({ taskId }: TaskHeaderProps) {
  const { taskMeta } = useTask();
  const { data: task } = useQuery({
    queryKey: taskKeys.detail(taskId),
    queryFn: () => getTask(taskId),
  });

  const title = getTaskDisplayTitle(taskMeta.title || task?.title || null);

  return (
    <header className={CHAT_HEADER_CLASS}>
      <TaskTitleMenu taskId={taskId} title={title} task={task} />
    </header>
  );
}
