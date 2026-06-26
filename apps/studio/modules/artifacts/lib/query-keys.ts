export const artifactKeys = {
  all: ["artifacts"] as const,
  detail: (id: string) => ["artifacts", id] as const,
};
