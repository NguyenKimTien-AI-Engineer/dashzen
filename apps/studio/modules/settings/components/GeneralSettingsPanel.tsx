"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, mapFieldErrors } from "@/lib/api/errors";
import { useUpdateProfile } from "@/modules/auth/hooks/useAccount";
import { useMe } from "@/modules/auth/hooks/useMe";
import { updateProfileSchema } from "@/modules/auth/schemas/account.schema";

function getUserInitial(displayName: string | null | undefined, email: string): string {
  const source = displayName?.trim() || email;
  return source.charAt(0).toUpperCase() || "?";
}

export function GeneralSettingsPanel() {
  const { data: user } = useMe();
  const updateProfileMutation = useUpdateProfile();
  const [displayName, setDisplayName] = useState("");
  const [displayNameError, setDisplayNameError] = useState<string | undefined>();

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name ?? "");
    }
  }, [user]);

  if (!user) return null;

  async function handleSave() {
    setDisplayNameError(undefined);
    const parsed = updateProfileSchema.safeParse({ display_name: displayName });
    if (!parsed.success) {
      setDisplayNameError(parsed.error.issues[0]?.message);
      return;
    }

    try {
      await updateProfileMutation.mutateAsync({ displayName: parsed.data.display_name });
      toast.success("Profile updated");
    } catch (error) {
      if (error instanceof ApiError) {
        const fieldErrors = mapFieldErrors(error.body.fields);
        if (fieldErrors.display_name) {
          setDisplayNameError(fieldErrors.display_name);
          return;
        }
        toast.error(error.message);
        return;
      }
      toast.error("Something went wrong. Please try again.");
    }
  }

  const initial = getUserInitial(user.display_name, user.email);
  const hasChanges = displayName.trim() !== (user.display_name?.trim() ?? "");

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-semibold tracking-tight">Profile</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your display name and how you appear in DashZen Studio.
        </p>
      </div>

      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Label className="w-32 shrink-0 text-sm text-muted-foreground">Avatar</Label>
          <span className="flex size-12 items-center justify-center rounded-full bg-foreground text-lg font-semibold text-background">
            {initial}
          </span>
        </div>

        <div className="space-y-2">
          <Label htmlFor="settings-display-name" className="text-sm text-muted-foreground">
            Full name
          </Label>
          <Input
            id="settings-display-name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            maxLength={100}
            className="max-w-md"
            aria-invalid={!!displayNameError}
          />
          {displayNameError ? (
            <p className="text-sm text-destructive">{displayNameError}</p>
          ) : null}
        </div>

        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">Member since</p>
          <p className="text-sm">
            {user.created_at ? new Date(user.created_at).toLocaleDateString("en-US") : "—"}
          </p>
        </div>
      </div>

      {hasChanges ? (
        <div className="flex justify-end gap-2 border-t pt-4">
          <Button
            variant="ghost"
            onClick={() => setDisplayName(user.display_name ?? "")}
            disabled={updateProfileMutation.isPending}
          >
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={updateProfileMutation.isPending}>
            {updateProfileMutation.isPending ? "Saving..." : "Save changes"}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
