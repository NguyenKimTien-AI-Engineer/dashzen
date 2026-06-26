"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";

import { clearSessionAndLogin, refreshSession } from "@/lib/api/client";
import { useMe } from "../hooks/useMe";
import { useSessionKeepAlive } from "../hooks/useSessionKeepAlive";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

function SessionExpiredScreen({ returnTo }: { returnTo: string }) {
  return (
    <div className="flex h-screen w-screen items-center justify-center p-4">
      <div className="w-full max-w-md space-y-4 rounded-xl border border-border bg-card p-6 text-center shadow-sm">
        <h1 className="text-lg font-semibold text-foreground">Session expired</h1>
        <p className="text-sm leading-relaxed text-muted-foreground">
          Your sign-in session is no longer valid. Your account is still saved — sign in
          again with the same email and password.
        </p>
        <Button
          className="w-full"
          onClick={() => {
            void clearSessionAndLogin(returnTo);
          }}
        >
          Sign in again
        </Button>
      </div>
    </div>
  );
}

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { data, isLoading, refetch } = useMe();
  const [recovering, setRecovering] = useState(false);
  const [sessionExpired, setSessionExpired] = useState(false);
  const recoveryStarted = useRef(false);

  useSessionKeepAlive();

  useEffect(() => {
    if (isLoading) return;

    if (data) {
      recoveryStarted.current = false;
      setSessionExpired(false);
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

      setSessionExpired(true);
    }

    void recoverSession();

    return () => {
      cancelled = true;
    };
  }, [isLoading, data, refetch]);

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

  if (sessionExpired) {
    return <SessionExpiredScreen returnTo={pathname} />;
  }

  if (!data) return null;

  return <>{children}</>;
}
