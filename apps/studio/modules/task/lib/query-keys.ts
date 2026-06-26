export const taskKeys = {
  all: ["tasks"] as const,
  detail: (taskId: string) => ["tasks", taskId] as const,
  messages: (taskId: string) => ["tasks", taskId, "messages"] as const,
  artifacts: (taskId: string) => ["tasks", taskId, "artifacts"] as const,
};
