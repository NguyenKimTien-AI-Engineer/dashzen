export type ArtifactListItem = {
  id: string;
  name: string;
  kind: string;
  size: number;
  task_id: string;
  task_title: string | null;
  task_type: string | null;
  created_at: string;
  edited_at: string;
};

export type ArtifactDetail = ArtifactListItem & {
  content: string | null;
  source: string;
};
