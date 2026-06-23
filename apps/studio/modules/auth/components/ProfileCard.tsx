"use client";

import Link from "next/link";
import { Badge } from "../../../components/ui/badge";
import { Input } from "../../../components/ui/input";
import { Label } from "../../../components/ui/label";
import type { User } from "../types/auth";

type ProfileCardProps = {
  user: User;
  editing?: boolean;
  displayName?: string;
  onDisplayNameChange?: (value: string) => void;
  displayNameError?: string;
};

export function ProfileCard({
  user,
  editing = false,
  displayName = "",
  onDisplayNameChange,
  displayNameError,
}: ProfileCardProps) {
  return (
    <div className="rounded-lg border bg-card shadow-sm">
      <dl className="divide-y">
        <div className="flex flex-col px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
          <dt className="text-sm font-medium text-muted-foreground sm:w-1/3">Email</dt>
          <dd className="mt-1 flex flex-wrap items-center gap-3 text-sm sm:col-span-2 sm:mt-0">
            {user.email}
            {user.email_verified ? (
              <Badge variant="secondary" className="bg-green-100 text-green-800 hover:bg-green-100">
                Verified
              </Badge>
            ) : (
              <>
                <Badge variant="destructive">Unverified</Badge>
                <Link
                  href={`/verify-email?email=${encodeURIComponent(user.email)}`}
                  className="text-sm font-medium text-primary hover:underline"
                >
                  Verify email
                </Link>
              </>
            )}
          </dd>
        </div>
        <div className="flex flex-col px-6 py-4 sm:flex-row sm:items-start sm:justify-between">
          <dt className="text-sm font-medium text-muted-foreground sm:w-1/3">Display name</dt>
          <dd className="mt-1 w-full text-sm sm:col-span-2 sm:mt-0 sm:max-w-sm">
            {editing ? (
              <div className="space-y-1">
                <Label htmlFor="display_name" className="sr-only">
                  Display name
                </Label>
                <Input
                  id="display_name"
                  value={displayName}
                  onChange={(e) => onDisplayNameChange?.(e.target.value)}
                  maxLength={100}
                  aria-invalid={!!displayNameError}
                  aria-describedby={displayNameError ? "display_name-error" : undefined}
                />
                {displayNameError ? (
                  <p id="display_name-error" className="text-sm text-destructive">
                    {displayNameError}
                  </p>
                ) : null}
              </div>
            ) : (
              user.display_name || "—"
            )}
          </dd>
        </div>
        <div className="flex flex-col px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
          <dt className="text-sm font-medium text-muted-foreground sm:w-1/3">Member since</dt>
          <dd className="mt-1 text-sm sm:col-span-2 sm:mt-0">
            {user.created_at ? new Date(user.created_at).toLocaleDateString("en-US") : "—"}
          </dd>
        </div>
      </dl>
    </div>
  );
}
