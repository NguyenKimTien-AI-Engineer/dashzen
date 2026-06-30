/**
 * Compact token count for UI (Thinking header, Settings).
 */
export function formatTokens(count: number): string {
  if (!Number.isFinite(count) || count < 0) return "0";
  if (count < 1_000) return count.toLocaleString("en-US");
  if (count < 1_000_000) {
    return `${trimTrailingZero((count / 1_000).toFixed(1))}K`;
  }
  return `${trimTrailingZero((count / 1_000_000).toFixed(1))}M`;
}

function trimTrailingZero(value: string): string {
  return value.endsWith(".0") ? value.slice(0, -2) : value;
}

export function formatUsagePair(input: number, output: number): string {
  return `In ${formatTokens(input)} · Out ${formatTokens(output)}`;
}
