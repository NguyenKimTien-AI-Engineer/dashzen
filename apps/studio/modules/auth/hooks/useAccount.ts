import { useMutation, useQueryClient } from "@tanstack/react-query";
import { changePassword, deleteAccount, deleteAvatar, updateProfile, uploadAvatar } from "@/lib/api/auth";
import { useAuthStore } from "@/lib/stores/authStore";
import type { User } from "../types/auth";

function syncUser(queryClient: ReturnType<typeof useQueryClient>, setUser: (user: User) => void, user: User) {
  setUser(user);
  queryClient.setQueryData(["auth", "me"], user);
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  const setUser = useAuthStore((state) => state.setUser);

  return useMutation({
    mutationFn: async ({ displayName }: { displayName: string }) => {
      return updateProfile(displayName);
    },
    onSuccess: (user: User) => {
      syncUser(queryClient, setUser, user);
    },
  });
}

export function useUploadAvatar() {
  const queryClient = useQueryClient();
  const setUser = useAuthStore((state) => state.setUser);

  return useMutation({
    mutationFn: (file: File) => uploadAvatar(file),
    onSuccess: (user: User) => {
      syncUser(queryClient, setUser, user);
    },
  });
}

export function useDeleteAvatar() {
  const queryClient = useQueryClient();
  const setUser = useAuthStore((state) => state.setUser);

  return useMutation({
    mutationFn: () => deleteAvatar(),
    onSuccess: (user: User) => {
      syncUser(queryClient, setUser, user);
    },
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: async ({
      currentPassword,
      newPassword,
    }: {
      currentPassword: string;
      newPassword: string;
    }) => {
      return changePassword(currentPassword, newPassword);
    },
  });
}

export function useDeleteAccount() {
  const queryClient = useQueryClient();
  const clear = useAuthStore((state) => state.clear);

  return useMutation({
    mutationFn: async ({
      password,
      confirmation,
    }: {
      password?: string;
      confirmation: "DELETE";
    }) => {
      return deleteAccount(confirmation, password);
    },
    onSuccess: () => {
      clear();
      queryClient.removeQueries({ queryKey: ["auth"] });
    },
  });
}
