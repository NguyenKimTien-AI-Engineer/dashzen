import {
  dehydrate,
  HydrationBoundary,
  QueryClient,
} from "@tanstack/react-query";
import { serverGetJson } from "@/lib/api/server";
import { ArtifactDetailClient } from "@/modules/artifacts/components/ArtifactDetailClient";
import { artifactKeys } from "@/modules/artifacts/lib/query-keys";
import type { ArtifactDetail } from "@/modules/artifacts/types/api";

type PageProps = {
  params: Promise<{ artifactId: string }>;
};

export default async function ArtifactDetailPage({ params }: PageProps) {
  const { artifactId } = await params;
  const queryClient = new QueryClient();

  await queryClient.prefetchQuery({
    queryKey: artifactKeys.detail(artifactId),
    queryFn: async () => {
      const data = await serverGetJson<ArtifactDetail>(`/v1/artifacts/${artifactId}`);
      if (!data) throw new Error("prefetch_failed");
      return data;
    },
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <ArtifactDetailClient />
    </HydrationBoundary>
  );
}
