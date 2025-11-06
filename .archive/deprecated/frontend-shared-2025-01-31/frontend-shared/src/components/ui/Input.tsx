// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.
//
import type { ForwardedRef, InputHTMLAttributes } from "react";
import { forwardRef } from "react";
import { cn } from "../../lib/utils";

type InputVariant = "subtle" | "default";

type InputProps = {
  isInvalid?: boolean;
  variant?: InputVariant;
} & InputHTMLAttributes<HTMLInputElement>;

const baseStyles = "flex h-10 w-full rounded-md px-3 py-2 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:cursor-not-allowed disabled:opacity-60";

const variantStyles: Record<InputVariant, string> = {
  subtle: "border border-transparent bg-secondary/20 text-white placeholder:text-secondary/60 focus-visible:ring-primary focus-visible:ring-offset-2",
  default: "border border-gray-300 bg-white text-gray-900 placeholder:text-gray-500 focus-visible:ring-primary focus-visible:ring-offset-0",
};

const invalidStyles: Record<InputVariant, string> = {
  subtle: "border-danger focus-visible:ring-danger focus-visible:ring-offset-2",
  default: "border-danger focus-visible:ring-danger focus-visible:ring-offset-0",
};

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, type = "text", isInvalid = false, variant = "default", ...props },
  ref: ForwardedRef<HTMLInputElement>
) {
  return (
    <input
      ref={ref}
      type={type}
      className={cn(
        baseStyles,
        variantStyles[variant],
        isInvalid ? invalidStyles[variant] : undefined,
        className
      )}
      {...props}
    />
  );
});
