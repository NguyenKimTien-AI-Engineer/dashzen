export function downloadTextFile(content: string, filename: string, mime = "text/plain;charset=utf-8") {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function downloadHtmlFile(html: string, filename = "dashboard.html") {
  downloadTextFile(html, filename, "text/html;charset=utf-8");
}

export function openHtmlInNewTab(html: string) {
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank", "noopener,noreferrer");
  window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

export async function copyTextToClipboard(text: string) {
  await navigator.clipboard.writeText(text);
}

export async function copyHtmlToClipboard(html: string) {
  await copyTextToClipboard(html);
}
