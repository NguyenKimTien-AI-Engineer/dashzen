import { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { AuthLayout } from "../../../modules/auth/components/AuthLayout";
import { LoginForm } from "../../../modules/auth/components/LoginForm";
import { Skeleton } from "../../../components/ui/skeleton";

export const metadata: Metadata = {
  title: "Sign in — DashZen",
  description: "Sign in to DashZen Studio",
  robots: "noindex, nofollow",
};

export default function LoginPage() {
  const footer = (
    <div className="text-sm text-muted-foreground">
      Don&apos;t have an account?{" "}
      <Link href="/register" className="font-medium text-primary hover:underline">
        Sign up
      </Link>
    </div>
  );

  return (
    <AuthLayout title="Sign in" description="Continue to DashZen Studio" footer={footer}>
      <Suspense fallback={<Skeleton className="h-48 w-full" />}>
        <LoginForm />
      </Suspense>
    </AuthLayout>
  );
}
