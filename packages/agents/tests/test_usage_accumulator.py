from __future__ import annotations

from agents.usage.accumulator import UsageAccumulator


def test_usage_accumulator_adds_tokens() -> None:
    acc = UsageAccumulator()
    acc.add(100, 50)
    acc.add(200, 25)
    assert acc.input_tokens == 300
    assert acc.output_tokens == 75
