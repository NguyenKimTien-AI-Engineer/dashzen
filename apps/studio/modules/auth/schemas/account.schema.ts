import { z } from "zod";

const passwordField = z
  .string()
  .min(8, "Password must be at least 8 characters")
  .regex(/[a-zA-Z]/, "Must contain a letter")
  .regex(/\d/, "Must contain a digit");

export const updateProfileSchema = z.object({
  display_name: z
    .string()
    .trim()
    .min(1, "Display name is required")
    .max(100, "Display name must be at most 100 characters"),
});

export type UpdateProfileFormData = z.infer<typeof updateProfileSchema>;

export const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, "Current password is required"),
    new_password: passwordField,
    confirm_password: z.string(),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  })
  .refine((data) => data.new_password !== data.current_password, {
    message: "New password must differ from current password",
    path: ["new_password"],
  });

export type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;

export const deleteAccountSchema = z.object({
  confirmation: z
    .string()
    .refine((value) => value === "DELETE", { message: "Type DELETE to confirm" }),
  password: z.string().min(1, "Password is required"),
});

export type DeleteAccountFormData = z.infer<typeof deleteAccountSchema>;
export type DeleteAccountFormInput = z.input<typeof deleteAccountSchema>;
