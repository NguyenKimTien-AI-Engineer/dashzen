import { useMutation, useQueryClient } from "@tanstack/react-query";
import { login, logoutApi, register } from "../../../lib/api/auth";
import { useAuthStore } from "../../../lib/stores/authStore";

export function useLogin() {
  const queryClient = useQueryClient();
  const setUser = useAuthStore((state) => state.setUser);

  return useMutation({
    mutationFn: async ({ email, password }: { email: string; password: string }) => {
      return login(email, password);
    },
    onSuccess: (data) => {
      setUser(data.user);
      queryClient.setQueryData(["auth", "me"], data.user);
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: async ({ email, password, displayName }: { email: string; password: string; displayName?: string }) => {
      return register(email, password, displayName);
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  const clear = useAuthStore((state) => state.clear);

  return useMutation({
    mutationFn: logoutApi,
    onSuccess: () => {
      clear();
      queryClient.removeQueries({ queryKey: ["auth"] });
    },
  });
}
