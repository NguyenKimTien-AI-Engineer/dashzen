/** Turn common LLM inline list patterns into valid markdown lists. */
export function normalizeMarkdownContent(content: string): string {
  let text = content.trim();
  if (!text) return text;

  // Normalize inline LaTeX arrows that models sometimes emit in plain text.
  text = text.replace(/\$\\rightarrow\$/g, "→");
  text = text.replace(/\\rightarrow/g, "→");

  // "đặc biệt là: - item - item" → start a markdown list
  text = text.replace(/([:.!?])\s+-\s+/g, "$1\n\n- ");

  // Split glued list items on the same line: "- a - b - c"
  text = text
    .split("\n")
    .map((line) => {
      if (/^\s*-\s/.test(line)) {
        return line.replace(/\s+-\s+/g, "\n- ");
      }
      if (/^\s*\d+\.\s/.test(line)) {
        return line.replace(/\s+(\d+)\.\s+/g, "\n$1. ");
      }
      return line;
    })
    .join("\n");

  text = text.replace(/\n{3,}/g, "\n\n");

  return text;
}
