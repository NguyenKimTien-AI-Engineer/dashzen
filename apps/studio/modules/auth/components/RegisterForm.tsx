"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { AlertCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { RegisterFormData, registerSchema } from "../schemas/auth.schema";
import { useRegister } from "../hooks/useAuth";
import { ApiError, mapFieldErrors } from "@/lib/api/errors";
import { GoogleSignInButton } from "./GoogleSignInButton";

export function RegisterForm() {
  const router = useRouter();
  const registerMutation = useRegister();
  const [globalError, setGlobalError] = useState<string | null>(null);

  const form = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: "",
      password: "",
      display_name: "",
    },
  });

  async function onSubmit(data: RegisterFormData) {
    setGlobalError(null);
    try {
      const res = await registerMutation.mutateAsync(data);
      if (res.requires_verification) {
        toast.success("We sent a verification code to your email.");
        router.push(`/verify-email?email=${encodeURIComponent(data.email)}`);
      } else {
        router.push("/app");
      }
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.code === "email_exists") {
          form.setError("email", { message: "This email is already in use" });
        } else if (error.code === "validation_error") {
          const fieldErrors = mapFieldErrors(error.body?.fields);
          Object.entries(fieldErrors).forEach(([field, msg]) => {
            if (field === "email" || field === "password" || field === "display_name") {
              form.setError(field, { message: msg });
            }
          });
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
      {globalError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{globalError}</AlertDescription>
        </Alert>
      )}

      <GoogleSignInButton disabled={registerMutation.isPending} />

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
            name="display_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Display name (optional)</FormLabel>
                <FormControl>
                  <Input type="text" placeholder="Jane Doe" {...field} />
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
                <p className="text-[0.8rem] text-muted-foreground">At least 8 characters, including letters and numbers</p>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button type="submit" className="w-full" disabled={registerMutation.isPending}>
            {registerMutation.isPending ? "Creating account..." : "Create account"}
          </Button>
        </form>
      </Form>
    </div>
  );
}
