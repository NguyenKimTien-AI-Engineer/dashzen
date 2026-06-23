"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { refreshSession } from "../../../lib/api/client";
import { useMe } from "../hooks/useMe";
import { useSessionKeepAlive } from "../hooks/useSessionKeepAlive";
import { Skeleton } from "../../../components/ui/skeleton";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { data, isLoading, refetch } = useMe();
  const [recovering, setRecovering] = useState(false);
  const recoveryStarted = useRef(false);

  useSessionKeepAlive();

  useEffect(() => {
    if (isLoading) return;

    if (data) {
      recoveryStarted.current = false;
      return;
    }

    if (recoveryStarted.current) return;
    recoveryStarted.current = true;

    let cancelled = false;

    async function recoverSession() {
      setRecovering(true);
      const refreshed = await refreshSession();
      if (cancelled) return;

      if (refreshed) {
        const result = await refetch();
        if (cancelled) return;
        setRecovering(false);
        if (result.data) return;
      } else {
        setRecovering(false);
      }

      router.replace(`/login?return_to=${encodeURIComponent(pathname)}`);
    }

    void recoverSession();

    return () => {
      cancelled = true;
    };
  }, [isLoading, data, pathname, router, refetch]);

  if (isLoading || recovering) {
    return (
      <div className="flex h-screen w-screen items-center justify-center p-4">
        <div className="w-full max-w-md space-y-4">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-12 w-3/4" />
        </div>
      </div>
    );
  }

  if (!data) return null;

  return <>{children}</>;
}
