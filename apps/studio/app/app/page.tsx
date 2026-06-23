"use client";

import { useMe } from "../../modules/auth/hooks/useMe";
import { Button } from "../../components/ui/button";
import Link from "next/link";

export default function AppPage() {
  const { data: user } = useMe();

  return (
    <div className="flex h-full flex-col items-center justify-center space-y-6 text-center">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Hello, {user?.display_name || user?.email}</h1>
        <p className="text-muted-foreground">Task chat will be available in the next phase</p>
      </div>
      <div className="flex items-center gap-4">
        <Link href="/app/settings">
          <Button>Go to Settings</Button>
        </Link>
      </div>
    </div>
  );
}
