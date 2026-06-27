"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { AlertCircle } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { LoginFormData, loginSchema } from "../schemas/auth.schema";
import { useLogin } from "../hooks/useAuth";
import { ApiError } from "@/lib/api/errors";
import { GoogleSignInButton } from "./GoogleSignInButton";

const OAUTH_ERROR_MESSAGES: Record<string, string> = {
  oauth_state_invalid: "Sign-in expired. Please try again.",
  oauth_exchange_failed: "Could not complete Google sign-in. Try again later.",
  google_email_unverified: "Your Google email is not verified.",
  account_exists_password:
    "An account with this email already exists. Sign in with your password first.",
};

function safeReturnTo(raw: string | null): string {
  if (!raw) return "/app";
  if (!raw.startsWith("/app")) return "/app";
  if (raw.startsWith("//")) return "/app";
  return raw;
}

export function LoginForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const loginMutation = useLogin();

  const [globalError, setGlobalError] = useState<string | null>(null);
  const [needsVerificationEmail, setNeedsVerificationEmail] = useState<string | null>(null);

  const verified = searchParams?.get("verified") === "1";
  const verifiedEmail = searchParams?.get("email");
  const returnTo = safeReturnTo(searchParams?.get("return_to") ?? null);

  useEffect(() => {
    const oauthError = searchParams?.get("error");
    if (!oauthError) return;
    const message = OAUTH_ERROR_MESSAGES[oauthError] ?? "Google sign-in failed. Please try again.";
    toast.error(message);
    router.replace("/login");
  }, [router, searchParams]);

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: verifiedEmail || "",
      password: "",
    },
  });

  async function onSubmit(data: LoginFormData) {
    setGlobalError(null);
    setNeedsVerificationEmail(null);

    try {
      await loginMutation.mutateAsync(data);
      window.location.assign(returnTo);
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.code === "invalid_credentials") {
          setGlobalError("Invalid email or password.");
        } else if (error.code === "email_not_verified") {
          setNeedsVerificationEmail(data.email);
        } else if (error.code === "user_inactive") {
          toast.error("Your account has been deactivated.");
        } else {
          setGlobalError(error.message);
        }
      } else {
        toast.error("Server connection error. Please try again later.");
      }
    }
  }

  return (
    <div className="space-y-4">
      {verified && (
        <Alert className="border-green-200 bg-green-50 text-green-900">
          <AlertDescription>Email verified — sign in to continue.</AlertDescription>
        </Alert>
      )}

      {globalError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{globalError}</AlertDescription>
        </Alert>
      )}

      {needsVerificationEmail && (
        <Alert className="border-yellow-200 bg-yellow-50 text-yellow-900">
          <AlertCircle className="h-4 w-4" color="#854d0e" />
          <AlertDescription className="flex flex-col gap-2">
            <span>Please verify your email before signing in.</span>
            <Link href={`/verify-email?email=${encodeURIComponent(needsVerificationEmail)}`}>
              <Button variant="link" className="h-auto p-0 font-normal text-yellow-800">
                Resend verification code
              </Button>
            </Link>
          </AlertDescription>
        </Alert>
      )}

      <GoogleSignInButton returnTo={returnTo} disabled={loginMutation.isPending} />

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-background px-2 text-muted-foreground">or continue with email</span>
        </div>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input type="email" placeholder="user@example.com" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Password</FormLabel>
                <FormControl>
                  <Input type="password" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button type="submit" className="w-full" disabled={loginMutation.isPending}>
            {loginMutation.isPending ? "Signing in..." : "Sign in"}
          </Button>
        </form>
      </Form>
    </div>
  );
}
