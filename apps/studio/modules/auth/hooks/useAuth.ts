import { useMutation, useQueryClient } from "@tanstack/react-query";
import { login, logoutApi, register } from "@/lib/api/auth";
import { useAuthStore } from "@/lib/stores/authStore";

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
    mutationFn: async ({
      email,
      password,
      display_name,
    }: {
      email: string;
      password: string;
      display_name?: string;
    }) => {
      return register(email, password, display_name);
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
