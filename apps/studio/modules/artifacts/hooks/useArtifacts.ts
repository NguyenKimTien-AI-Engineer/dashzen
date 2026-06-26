"use client";

import { useQuery } from "@tanstack/react-query";
import { getArtifact, listArtifacts } from "@/lib/api/artifacts";
import { artifactKeys } from "@/modules/artifacts/lib/query-keys";

export function useArtifacts() {
  return useQuery({
    queryKey: artifactKeys.all,
    queryFn: listArtifacts,
  });
}

export function useArtifact(id: string) {
  return useQuery({
    queryKey: artifactKeys.detail(id),
    queryFn: () => getArtifact(id),
    enabled: Boolean(id),
  });
}
