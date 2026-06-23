import { AuthGuard } from "../../modules/auth/components/AuthGuard";
import { AppShell } from "../../modules/layout/components/AppShell";

export default function AppLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <AuthGuard>
      <div className="flex h-screen bg-background">
        <AppShell>{children}</AppShell>
      </div>
    </AuthGuard>
  );
}
