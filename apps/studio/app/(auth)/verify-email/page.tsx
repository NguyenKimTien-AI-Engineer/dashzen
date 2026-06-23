import { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { AuthLayout } from "../../../modules/auth/components/AuthLayout";
import { VerifyEmailForm } from "../../../modules/auth/components/VerifyEmailForm";
import { Skeleton } from "../../../components/ui/skeleton";

export const metadata: Metadata = {
  title: "Verify email — DashZen",
  description: "Verify your email address",
  robots: "noindex, nofollow",
};

export default function VerifyEmailPage() {
  const footer = (
    <div className="text-sm text-muted-foreground">
      <Link href="/login" className="font-medium text-primary hover:underline">
        Back to sign in
      </Link>
    </div>
  );

  return (
    <AuthLayout title="Verify email" footer={footer}>
      <Suspense fallback={<Skeleton className="h-48 w-full" />}>
        <VerifyEmailForm />
      </Suspense>
    </AuthLayout>
  );
}
