import {
  dehydrate,
  HydrationBoundary,
  QueryClient,
} from "@tanstack/react-query";
import { serverGetJson } from "@/lib/api/server";
import { ProjectDetailClient } from "@/modules/project/components/ProjectDetailClient";
import { projectKeys } from "@/modules/project/lib/query-keys";
import type { Project } from "@/modules/project/types/api";
import type { Task } from "@/modules/task/types/api";

type PageProps = {
  params: Promise<{ projectId: string }>;
};

export default async function ProjectDetailPage({ params }: PageProps) {
  const { projectId } = await params;
  const queryClient = new QueryClient();

  await Promise.all([
    queryClient.prefetchQuery({
      queryKey: projectKeys.detail(projectId),
      queryFn: async () => {
        const data = await serverGetJson<Project>(`/v1/projects/${projectId}`);
        if (!data) throw new Error("prefetch_failed");
        return data;
      },
    }),
    queryClient.prefetchQuery({
      queryKey: projectKeys.tasks(projectId),
      queryFn: async () => {
        const data = await serverGetJson<Task[]>(`/v1/projects/${projectId}/tasks`);
        if (!data) throw new Error("prefetch_failed");
        return data;
      },
    }),
  ]);

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <ProjectDetailClient />
    </HydrationBoundary>
  );
}
