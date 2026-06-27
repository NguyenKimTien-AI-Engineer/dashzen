"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { AlertCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { OtpInput } from "./OtpInput";
import { VerifyEmailFormData, verifyEmailSchema } from "../schemas/auth.schema";
import { useResendVerification, useVerifyEmail } from "../hooks/useVerifyEmail";
import { ApiError } from "@/lib/api/errors";

export function VerifyEmailForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const verifyMutation = useVerifyEmail();
  const resendMutation = useResendVerification();

  const [globalError, setGlobalError] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);

  const emailParam = searchParams?.get("email");

  const form = useForm<VerifyEmailFormData>({
    resolver: zodResolver(verifyEmailSchema),
    defaultValues: {
      email: emailParam || "",
      code: "",
    },
  });

  useEffect(() => {
    if (cooldown > 0) {
      const timer = setTimeout(() => setCooldown(cooldown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [cooldown]);

  async function onSubmit(data: VerifyEmailFormData) {
    setGlobalError(null);
    try {
      await verifyMutation.mutateAsync(data);
      toast.success("Email verified successfully");
      router.push(`/login?verified=1&email=${encodeURIComponent(data.email)}`);
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.code === "invalid_code") {
          form.setError("code", { message: "Invalid or expired code" });
          form.setValue("code", "");
        } else if (error.code === "too_many_attempts") {
          setGlobalError("Too many failed attempts. Please request a new code.");
          form.setValue("code", "");
        } else if (error.code === "already_verified") {
          toast.info("This email is already verified.");
          router.push(`/login?email=${encodeURIComponent(data.email)}`);
        } else {
          setGlobalError(error.message);
        }
      } else {
        toast.error("Connection error. Please try again.");
      }
    }
  }

  async function handleResend() {
    const email = form.getValues("email");
    if (!email) {
      form.trigger("email");
      return;
    }

    try {
      await resendMutation.mutateAsync(email);
      toast.success("A new code has been sent");
      setCooldown(60);
      form.setValue("code", "");
      setGlobalError(null);
    } catch (error) {
      if (error instanceof ApiError && error.status === 429) {
        const retryAfter = error.body?.message?.match(/(\d+)/)?.[0];
        setCooldown(retryAfter ? parseInt(retryAfter, 10) : 60);
      } else if (error instanceof ApiError && error.code === "already_verified") {
        toast.info("This email is already verified.");
        router.push(`/login?email=${encodeURIComponent(email)}`);
      } else {
        toast.error("Failed to resend code. Please try again later.");
      }
    }
  }

  return (
    <div className="space-y-6">
      {globalError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{globalError}</AlertDescription>
        </Alert>
      )}

      {process.env.NODE_ENV === "development" && (
        <Alert className="border-blue-200 bg-blue-50 text-blue-900">
          <AlertDescription>
            Dev: Open <a href="http://localhost:8025" target="_blank" className="font-medium underline">Mailpit</a> to view the OTP.
          </AlertDescription>
        </Alert>
      )}

      <div className="text-center text-sm text-muted-foreground">
        Enter the 6-digit code we sent to {emailParam ? <strong>{emailParam}</strong> : "your email"}
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          {!emailParam && (
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input type="email" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          )}

          <FormField
            control={form.control}
            name="code"
            render={({ field }) => (
              <FormItem>
                <FormControl>
                  <OtpInput {...field} />
                </FormControl>
                <FormMessage className="text-center" />
              </FormItem>
            )}
          />

          <Button type="submit" className="w-full" disabled={verifyMutation.isPending || form.watch("code").length !== 6}>
            {verifyMutation.isPending ? "Verifying..." : "Confirm"}
          </Button>
        </form>
      </Form>

      <div className="flex flex-col items-center gap-2">
        <Button
          variant="outline"
          className="w-full"
          onClick={handleResend}
          disabled={cooldown > 0 || resendMutation.isPending}
          type="button"
        >
          {resendMutation.isPending ? "Sending..." : cooldown > 0 ? `Resend code (${cooldown}s)` : "Resend code"}
        </Button>
      </div>
    </div>
  );
}
