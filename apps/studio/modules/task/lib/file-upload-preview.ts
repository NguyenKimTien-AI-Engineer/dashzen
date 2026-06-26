export type FilePreviewKind = "image" | "pdf" | "document" | "spreadsheet" | "data" | "other";

const EXTENSION_LABELS: Record<string, string> = {
  pdf: "PDF",
  doc: "DOC",
  docx: "DOCX",
  txt: "TXT",
  md: "MD",
  rtf: "RTF",
  csv: "CSV",
  xls: "XLS",
  xlsx: "XLSX",
  json: "JSON",
  xml: "XML",
  yaml: "YAML",
  yml: "YML",
  ppt: "PPT",
  pptx: "PPTX",
  zip: "ZIP",
};

export function getFileExtension(filename: string): string {
  const dot = filename.lastIndexOf(".");
  if (dot <= 0) return "";
  return filename.slice(dot + 1).toLowerCase();
}

export function getFilePreviewKind(file: File): FilePreviewKind {
  if (file.type.startsWith("image/")) return "image";

  const ext = getFileExtension(file.name);
  if (ext === "pdf" || file.type === "application/pdf") return "pdf";
  if (["doc", "docx", "txt", "md", "rtf"].includes(ext)) return "document";
  if (["xls", "xlsx", "csv"].includes(ext)) return "spreadsheet";
  if (["json", "xml", "yaml", "yml"].includes(ext)) return "data";
  return "other";
}

export function getFileTypeLabel(file: File): string {
  const ext = getFileExtension(file.name);
  if (EXTENSION_LABELS[ext]) return EXTENSION_LABELS[ext];
  if (ext) return ext.toUpperCase().slice(0, 4);
  if (file.type) {
    const subtype = file.type.split("/")[1]?.toUpperCase();
    if (subtype) return subtype.slice(0, 4);
  }
  return "FILE";
}

export function getDisplayFileName(filename: string): string {
  const base = filename.split(/[/\\]/).pop() ?? filename;
  const dot = base.lastIndexOf(".");
  return dot > 0 ? base.slice(0, dot) : base;
}
