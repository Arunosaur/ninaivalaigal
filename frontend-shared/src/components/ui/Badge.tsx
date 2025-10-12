import type { ForwardedRef, HTMLAttributes } from "react";
import { forwardRef } from "react";
import { cn } from "../../lib/utils";

type BadgeVariant =
  | "neutral"
  | "info"
  | "success"
  | "warning"
  | "danger"
  | "accent"
  | "primary";

type BadgeProps = {
  variant?: BadgeVariant;
  pill?: boolean;
} & HTMLAttributes<HTMLSpanElement>;

const badgeStyles: Record<BadgeVariant, string> = {
  neutral: "border-slate-200 bg-slate-100 text-slate-700 dark:border-slate-700 dark:bg-slate-900/60 dark:text-slate-200",
  info: "border-blue-200 bg-blue-100 text-blue-800 dark:border-blue-500/40 dark:bg-blue-500/10 dark:text-blue-200",
  success: "border-emerald-200 bg-emerald-100 text-emerald-800 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-200",
  warning: "border-amber-200 bg-amber-100 text-amber-800 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-200",
  danger: "border-rose-200 bg-rose-100 text-rose-800 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-200",
  accent: "border-violet-200 bg-violet-100 text-violet-800 dark:border-violet-500/40 dark:bg-violet-500/10 dark:text-violet-200",
  primary: "border-primary/30 bg-primary/10 text-primary dark:border-primary/40 dark:bg-primary/15 dark:text-primary"
};

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(function Badge(
  { className, children, variant = "neutral", pill = false, ...props },
  ref: ForwardedRef<HTMLSpanElement>
) {
  return (
    <span
      ref={ref}
      className={cn(
        "inline-flex items-center gap-1 border px-2 py-0.5 text-xs font-medium",
        pill ? "rounded-full" : "rounded-md",
        badgeStyles[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
});
