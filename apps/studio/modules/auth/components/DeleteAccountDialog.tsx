"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { Button } from "../../../components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../../../components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "../../../components/ui/form";
import { Input } from "../../../components/ui/input";
import { ApiError, mapFieldErrors } from "../../../lib/api/errors";
import { useDeleteAccount } from "../hooks/useAccount";
import {
  DeleteAccountFormInput,
  deleteAccountSchema,
} from "../schemas/account.schema";

type DeleteAccountDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export function DeleteAccountDialog({ open, onOpenChange }: DeleteAccountDialogProps) {
  const router = useRouter();
  const deleteAccountMutation = useDeleteAccount();

  const form = useForm<DeleteAccountFormInput>({
    resolver: zodResolver(deleteAccountSchema),
    defaultValues: {
      confirmation: "",
      password: "",
    },
  });

  const confirmation = form.watch("confirmation");
  const password = form.watch("password");
  const canSubmit =
    confirmation === "DELETE" && password.length > 0 && !deleteAccountMutation.isPending;

  function handleOpenChange(next: boolean) {
    if (!next) {
      form.reset();
    }
    onOpenChange(next);
  }

  async function onSubmit(data: DeleteAccountFormInput) {
    try {
      await deleteAccountMutation.mutateAsync({
        password: data.password,
        confirmation: "DELETE",
      });
      toast.success("Your account has been deleted");
      handleOpenChange(false);
      router.push("/login");
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.code === "invalid_credentials") {
          form.setError("password", { message: "Password is incorrect" });
          return;
        }
        const fieldErrors = mapFieldErrors(error.body.fields);
        for (const [field, message] of Object.entries(fieldErrors)) {
          if (field in form.getValues()) {
            form.setError(field as keyof DeleteAccountFormInput, { message });
          }
        }
        if (!error.body.fields?.length) {
          toast.error(error.message);
        }
        return;
      }
      toast.error("Something went wrong. Please try again.");
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete account</DialogTitle>
          <DialogDescription>
            This will permanently delete your account and all associated data. This action
            cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="confirmation"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Type DELETE to confirm</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      autoComplete="off"
                      placeholder="DELETE"
                    />
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
                  <FormLabel>Enter your password</FormLabel>
                  <FormControl>
                    <Input type="password" autoComplete="current-password" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button
                type="button"
                variant="ghost"
                onClick={() => handleOpenChange(false)}
                disabled={deleteAccountMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="destructive"
                disabled={!canSubmit}
              >
                {deleteAccountMutation.isPending ? "Deleting..." : "Delete my account"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
