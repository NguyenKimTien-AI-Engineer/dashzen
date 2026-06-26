import { useMutation } from "@tanstack/react-query";
import { resendVerification, verifyEmail } from "@/lib/api/auth";

export function useVerifyEmail() {
  return useMutation({
    mutationFn: async ({ email, code }: { email: string; code: string }) => {
      return verifyEmail(email, code);
    },
  });
}

export function useResendVerification() {
  return useMutation({
    mutationFn: async (email: string) => {
      return resendVerification(email);
    },
  });
}
