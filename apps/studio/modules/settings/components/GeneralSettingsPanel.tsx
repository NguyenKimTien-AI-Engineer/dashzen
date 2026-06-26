"use client";

import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { Camera, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api/errors";
import { UserAvatar } from "@/modules/auth/components/UserAvatar";
import { useDeleteAvatar, useUpdateProfile, useUploadAvatar } from "@/modules/auth/hooks/useAccount";
import { useMe } from "@/modules/auth/hooks/useMe";
import { updateProfileSchema } from "@/modules/auth/schemas/account.schema";

const ACCEPTED_AVATAR_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_AVATAR_BYTES = 2 * 1024 * 1024;

export function GeneralSettingsPanel() {
  const { data: user } = useMe();
  const updateProfileMutation = useUpdateProfile();
  const uploadAvatarMutation = useUploadAvatar();
  const deleteAvatarMutation = useDeleteAvatar();
  const fileInputRef = useRef<HTMLInputElement>(null);
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
        toast.error(error.message);
        return;
      }
      toast.error("Something went wrong. Please try again.");
    }
  }

  async function handleAvatarSelected(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    if (!ACCEPTED_AVATAR_TYPES.includes(file.type)) {
      toast.error("Please choose a JPEG, PNG, or WebP image.");
      return;
    }
    if (file.size > MAX_AVATAR_BYTES) {
      toast.error("Image must be 2MB or smaller.");
      return;
    }

    try {
      await uploadAvatarMutation.mutateAsync(file);
      toast.success("Avatar updated");
    } catch (error) {
      if (error instanceof ApiError) {
        toast.error(error.message);
        return;
      }
      toast.error("Could not upload avatar. Please try again.");
    }
  }

  async function handleRemoveAvatar() {
    try {
      await deleteAvatarMutation.mutateAsync();
      toast.success("Avatar removed");
    } catch (error) {
      if (error instanceof ApiError) {
        toast.error(error.message);
        return;
      }
      toast.error("Could not remove avatar. Please try again.");
    }
  }

  const hasChanges = displayName.trim() !== (user.display_name?.trim() ?? "");
  const avatarBusy = uploadAvatarMutation.isPending || deleteAvatarMutation.isPending;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-semibold tracking-tight">Profile</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your display name and how you appear in DashZen Studio.
        </p>
      </div>

      <div className="space-y-6">
        <div className="flex flex-wrap items-center gap-4">
          <Label className="w-32 shrink-0 text-sm text-muted-foreground">Avatar</Label>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={avatarBusy}
              className="group relative rounded-full disabled:opacity-50"
              aria-label="Change avatar"
            >
              <UserAvatar
                displayName={user.display_name}
                email={user.email}
                avatarUrl={user.avatar_url}
                size="md"
              />
              <span className="absolute inset-0 flex items-center justify-center rounded-full bg-black/50 opacity-0 transition-opacity group-hover:opacity-100">
                <Camera className="size-5 text-white" />
              </span>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED_AVATAR_TYPES.join(",")}
              className="hidden"
              onChange={handleAvatarSelected}
            />
            <div className="flex flex-col gap-1">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                disabled={avatarBusy}
              >
                {uploadAvatarMutation.isPending ? "Uploading..." : "Upload photo"}
              </Button>
              {user.avatar_url ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleRemoveAvatar}
                  disabled={avatarBusy}
                  className="justify-start text-muted-foreground"
                >
                  <Trash2 className="size-4" />
                  Remove
                </Button>
              ) : null}
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="settings-display-name" className="text-sm text-muted-foreground">
            Display name
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
