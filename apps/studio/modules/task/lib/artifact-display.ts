import type { ArtifactCanvasKind } from "@/lib/stores/artifactCanvasStore";

export function getArtifactKindFromFilename(filename: string): ArtifactCanvasKind {
  if (filename.endsWith(".html")) return "html";
  return "markdown";
}

export function getWorkspaceArtifactTitle(filename: string): string {
  switch (filename) {
    case "spec.md":
      return "Dashboard spec";
    case "bindings.md":
      return "Data bindings";
    case "layout.md":
      return "Layout design";
    case "dashboard.html":
      return "Dashboard";
    default:
      return filename.replace(/\.(md|html)$/i, "").replace(/[-_]/g, " ");
  }
}

export function getArtifactSubtitle(kind: ArtifactCanvasKind): string {
  return kind === "html" ? "Code · HTML" : "Document · Markdown";
}

export function getArtifactCanvasKindLabel(kind: ArtifactCanvasKind): string {
  return kind === "html" ? "HTML" : "Markdown";
}
