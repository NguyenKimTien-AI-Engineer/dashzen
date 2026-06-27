"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ChangePasswordDialog } from "@/modules/auth/components/ChangePasswordDialog";
import { DeleteAccountDialog } from "@/modules/auth/components/DeleteAccountDialog";
import { useLogout } from "@/modules/auth/hooks/useAuth";
import { useMe } from "@/modules/auth/hooks/useMe";
import { useSettingsPanelStore } from "@/lib/stores/settingsPanelStore";

export function AccountSettingsPanel() {
  const router = useRouter();
  const { data: user } = useMe();
  const logoutMutation = useLogout();
  const closePanel = useSettingsPanelStore((state) => state.closePanel);
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);
  const [deleteAccountOpen, setDeleteAccountOpen] = useState(false);

  if (!user) return null;

  function handleLogout() {
    logoutMutation.mutate(undefined, {
      onSuccess: () => {
        closePanel();
        router.push("/login");
      },
    });
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-semibold tracking-tight">Account</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Email, security, and session settings for your account.
        </p>
      </div>

      <div className="space-y-6">
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">Email</p>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm">{user.email}</span>
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
                  onClick={closePanel}
                >
                  Verify email
                </Link>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between gap-4 border-t pt-6">
          <div>
            <p className="text-sm font-medium">Password</p>
            <p className="text-sm text-muted-foreground">
              {user.has_password
                ? "Update your password to keep your account secure."
                : "You signed in with Google. Password login is not enabled for this account."}
            </p>
          </div>
          {user.has_password ? (
            <Button variant="outline" onClick={() => setChangePasswordOpen(true)}>
              Change password
            </Button>
          ) : null}
        </div>

        <div className="flex items-center justify-between gap-4 border-t pt-6">
          <div>
            <p className="text-sm font-medium">Sign out</p>
            <p className="text-sm text-muted-foreground">Sign out of this device.</p>
          </div>
          <Button variant="destructive" onClick={handleLogout} disabled={logoutMutation.isPending}>
            {logoutMutation.isPending ? "Signing out..." : "Sign out"}
          </Button>
        </div>

        <div className="rounded-lg border border-destructive/30 p-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-destructive">Delete account</p>
              <p className="text-sm text-muted-foreground">
                Permanently delete your account and all associated data.
              </p>
            </div>
            <Button variant="destructive" onClick={() => setDeleteAccountOpen(true)}>
              Delete account
            </Button>
          </div>
        </div>
      </div>

      <ChangePasswordDialog open={changePasswordOpen} onOpenChange={setChangePasswordOpen} />
      <DeleteAccountDialog
        open={deleteAccountOpen}
        onOpenChange={setDeleteAccountOpen}
        requiresPassword={user.has_password}
      />
    </div>
  );
}
