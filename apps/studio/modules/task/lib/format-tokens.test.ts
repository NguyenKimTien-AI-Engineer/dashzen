import { describe, expect, it } from "vitest";
import { formatTokens, formatUsagePair } from "./format-tokens";

describe("formatTokens", () => {
  it("formats small numbers", () => {
    expect(formatTokens(0)).toBe("0");
    expect(formatTokens(842)).toBe("842");
  });

  it("formats thousands", () => {
    expect(formatTokens(1_200)).toBe("1.2K");
    expect(formatTokens(12_400)).toBe("12.4K");
  });

  it("formats millions", () => {
    expect(formatTokens(1_500_000)).toBe("1.5M");
  });
});

describe("formatUsagePair", () => {
  it("combines input and output", () => {
    expect(formatUsagePair(12_400, 1_850)).toBe("In 12.4K · Out 1.9K");
  });
});
