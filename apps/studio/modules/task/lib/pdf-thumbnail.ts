export async function renderPdfThumbnail(file: File, width = 152): Promise<string | null> {
  try {
    const pdfjs = await import("pdfjs-dist");
    pdfjs.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

    const data = await file.arrayBuffer();
    const pdf = await pdfjs.getDocument({ data }).promise;
    const page = await pdf.getPage(1);
    const viewport = page.getViewport({ scale: 1 });
    const scale = width / viewport.width;
    const scaled = page.getViewport({ scale });

    const canvas = document.createElement("canvas");
    canvas.width = Math.floor(scaled.width);
    canvas.height = Math.floor(scaled.height);
    const context = canvas.getContext("2d");
    if (!context) return null;

    await page.render({ canvasContext: context, viewport: scaled }).promise;
    return canvas.toDataURL("image/jpeg", 0.82);
  } catch {
    return null;
  }
}
