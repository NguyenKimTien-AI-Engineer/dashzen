import { describe, expect, it } from "vitest";
import { isChatLayoutPath } from "@/modules/layout/lib/routes";

describe("isChatLayoutPath", () => {
  it("matches chat routes", () => {
    expect(isChatLayoutPath("/app")).toBe(true);
    expect(isChatLayoutPath("/app/chats")).toBe(true);
    expect(isChatLayoutPath("/app/task/abc")).toBe(true);
    expect(isChatLayoutPath("/app/projects/p1")).toBe(true);
  });

  it("rejects non-chat routes", () => {
    expect(isChatLayoutPath("/app/settings")).toBe(false);
    expect(isChatLayoutPath("/login")).toBe(false);
  });
});
