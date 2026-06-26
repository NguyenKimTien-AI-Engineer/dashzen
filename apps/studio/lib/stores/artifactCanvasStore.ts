import { create } from "zustand";

export type ArtifactCanvasView = "preview" | "code";
export type ArtifactCanvasKind = "html" | "markdown";

export type ArtifactCanvasPayload = {
  title: string;
  content: string;
  filename: string;
  kind: ArtifactCanvasKind;
};

type ArtifactCanvasStore = {
  open: boolean;
  title: string;
  content: string;
  filename: string;
  kind: ArtifactCanvasKind;
  view: ArtifactCanvasView;
  fullscreen: boolean;
  refreshKey: number;
  openCanvas: (payload: ArtifactCanvasPayload) => void;
  closeCanvas: () => void;
  setView: (view: ArtifactCanvasView) => void;
  setFullscreen: (fullscreen: boolean) => void;
  refresh: () => void;
};

export const useArtifactCanvasStore = create<ArtifactCanvasStore>((set) => ({
  open: false,
  title: "Dashboard",
  content: "",
  filename: "dashboard.html",
  kind: "html",
  view: "preview",
  fullscreen: false,
  refreshKey: 0,
  openCanvas: ({ title, content, filename, kind }) =>
    set({
      open: true,
      title,
      content,
      filename,
      kind,
      view: "preview",
      fullscreen: false,
    }),
  closeCanvas: () => set({ open: false, fullscreen: false }),
  setView: (view) => set({ view }),
  setFullscreen: (fullscreen) => set({ fullscreen }),
  refresh: () => set((state) => ({ refreshKey: state.refreshKey + 1 })),
}));
