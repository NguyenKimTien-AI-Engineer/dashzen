"""Token budget constants — single source of truth for FE and BE."""

LLM_CONTEXT_WINDOW = 128_000
_OUTPUT_RESERVE = 8_000
INPUT_BUDGET_TOKENS = LLM_CONTEXT_WINDOW - _OUTPUT_RESERVE

MICRO_COMPACT_FRACTION = 0.60
SUMMARY_COMPACT_FRACTION = 0.80
KEEP_TOKENS = 40_000
INITIAL_TOKENS_PER_CHAR: float = 0.34
IMAGE_CHAR_EQUIV = 6_000

MICRO_COMPACT_AT_TOKENS = int(INPUT_BUDGET_TOKENS * MICRO_COMPACT_FRACTION)
SUMMARY_COMPACT_AT_TOKENS = int(INPUT_BUDGET_TOKENS * SUMMARY_COMPACT_FRACTION)


def budget_response() -> dict[str, object]:
    return {
        "contextWindow": LLM_CONTEXT_WINDOW,
        "inputBudgetTokens": INPUT_BUDGET_TOKENS,
        "microCompactFraction": MICRO_COMPACT_FRACTION,
        "summaryCompactFraction": SUMMARY_COMPACT_FRACTION,
        "keepTokens": KEEP_TOKENS,
        "initialTokensPerChar": INITIAL_TOKENS_PER_CHAR,
        "imageCharEquiv": IMAGE_CHAR_EQUIV,
    }
