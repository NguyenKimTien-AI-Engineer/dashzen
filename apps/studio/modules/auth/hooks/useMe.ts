import { useQuery } from "@tanstack/react-query";
import { getMe } from "../../../lib/api/auth";

export function useMe() {
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: getMe,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}
