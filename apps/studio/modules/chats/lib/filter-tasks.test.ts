import { describe, expect, it } from "vitest";
import { filterTasks } from "@/modules/chats/lib/filter-tasks";
import type { Task } from "@/modules/task/types/api";

function makeTask(overrides: Partial<Task> = {}): Task {
  return {
    id: "t1",
    title: "Sales dashboard",
    status: "active",
    starred: false,
    type: null,
    project_id: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-02T00:00:00Z",
    ...overrides,
  };
}

describe("filterTasks", () => {
  const tasks = [
    makeTask({ id: "t1", title: "Alpha", updated_at: "2026-01-03T00:00:00Z" }),
    makeTask({ id: "t2", title: "Beta chat", status: "archived", updated_at: "2026-01-02T00:00:00Z" }),
  ];

  it("filters by active status", () => {
    const result = filterTasks(tasks, "", "active");
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("t1");
  });

  it("filters by search query", () => {
    const result = filterTasks(tasks, "beta", "all");
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("t2");
  });

  it("sorts by updated_at descending", () => {
    const result = filterTasks(tasks, "", "all");
    expect(result.map((t) => t.id)).toEqual(["t1", "t2"]);
  });
});
