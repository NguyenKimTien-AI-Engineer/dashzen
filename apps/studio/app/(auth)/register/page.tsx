import { Metadata } from "next";
import Link from "next/link";
import { AuthLayout } from "@/modules/auth/components/AuthLayout";
import { RegisterForm } from "@/modules/auth/components/RegisterForm";

export const metadata: Metadata = {
  title: "Sign up — DashZen",
  description: "Create a DashZen Studio account",
  robots: "noindex, nofollow",
};

export default function RegisterPage() {
  const footer = (
    <div className="text-sm text-muted-foreground">
      Already have an account?{" "}
      <Link href="/login" className="font-medium text-primary hover:underline">
        Sign in
      </Link>
    </div>
  );

  return (
    <AuthLayout title="Create account" description="Get started with DashZen Studio" footer={footer}>
      <RegisterForm />
    </AuthLayout>
  );
}
