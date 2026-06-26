import { TaskPageClient } from "@/modules/task/components/TaskPageClient";

type PageProps = {
  params: Promise<{ taskId: string }>;
};

export default async function TaskPage({ params }: PageProps) {
  const { taskId } = await params;
  return <TaskPageClient taskId={taskId} />;
}
