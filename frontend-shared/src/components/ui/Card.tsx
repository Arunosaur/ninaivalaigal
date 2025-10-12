import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/utils";

export type CardProps = HTMLAttributes<HTMLDivElement> & {
  title?: string;
  subtitle?: string;
  footer?: ReactNode;
};

export function Card({ className, title, subtitle, footer, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-white/5 bg-secondary/30 p-6 shadow-lg backdrop-blur-sm",
        className
      )}
      {...props}
    >
      {title ? <h3 className="text-lg font-semibold text-white">{title}</h3> : null}
      {subtitle ? <p className="mt-1 text-sm text-secondary/70">{subtitle}</p> : null}
      <div className={cn(title || subtitle ? "mt-4" : undefined)}>{children}</div>
      {footer ? <div className="mt-6 border-t border-white/10 pt-4 text-sm text-secondary/60">{footer}</div> : null}
    </div>
  );
}
