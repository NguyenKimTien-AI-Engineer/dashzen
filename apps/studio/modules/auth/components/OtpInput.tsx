"use client";

import { forwardRef } from "react";
import { Input } from "../../../components/ui/input";

export const OtpInput = forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => {
    return (
      <Input
        ref={ref}
        type="text"
        inputMode="numeric"
        autoComplete="one-time-code"
        maxLength={6}
        placeholder="••••••"
        className={`text-center text-2xl tracking-widest ${className || ""}`}
        onChange={(e) => {
          // Allow only numbers
          e.target.value = e.target.value.replace(/\D/g, "");
          if (props.onChange) {
            props.onChange(e);
          }
        }}
        {...props}
      />
    );
  }
);

OtpInput.displayName = "OtpInput";
