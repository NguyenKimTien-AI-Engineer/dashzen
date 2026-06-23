export function PrivacySettingsPanel() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-semibold tracking-tight">Privacy</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Control how your data is used in DashZen Studio.
        </p>
      </div>

      <div className="space-y-6">
        <div className="space-y-2">
          <p className="text-sm font-medium">Data usage</p>
          <p className="max-w-lg text-sm text-muted-foreground">
            DashZen stores your account information and dashboard data to provide the service.
            Prompts and generated content are processed to build your dashboards.
          </p>
        </div>

        <div className="space-y-2 border-t pt-6">
          <p className="text-sm font-medium">Session cookies</p>
          <p className="max-w-lg text-sm text-muted-foreground">
            Authentication uses secure httpOnly cookies. We do not store JWT tokens in
            browser localStorage.
          </p>
        </div>

        <div className="space-y-2 border-t pt-6">
          <p className="text-sm font-medium">Export & deletion</p>
          <p className="max-w-lg text-sm text-muted-foreground">
            You can delete your account at any time from the Account tab. Data export will be
            available in a future release.
          </p>
        </div>
      </div>
    </div>
  );
}
