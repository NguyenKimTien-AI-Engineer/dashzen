import { toast } from "sonner";

/** Show a stream/agent error as a Sonner toast (not inline in chat). */
export function showStreamErrorToast(message: string, retry?: () => void): void {
  toast.error(message, {
    duration: 10_000,
    action: retry
      ? {
          label: "Retry",
          onClick: retry,
        }
      : undefined,
  });
}
