import { fetchWithAuth } from "./client";
import type { ArtifactDetail, ArtifactListItem } from "@/modules/artifacts/types/api";

export async function listArtifacts(): Promise<ArtifactListItem[]> {
  const res = await fetchWithAuth("/v1/artifacts");
  return res.json() as Promise<ArtifactListItem[]>;
}

export async function getArtifact(id: string): Promise<ArtifactDetail> {
  const res = await fetchWithAuth(`/v1/artifacts/${id}`);
  return res.json() as Promise<ArtifactDetail>;
}
