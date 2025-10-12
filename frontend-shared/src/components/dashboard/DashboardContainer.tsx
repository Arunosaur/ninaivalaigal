import type { ReactNode } from "react";
import { Card } from "../ui/Card";
import { cn } from "../../lib/utils";

export type DashboardContainerProps = {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
};

export function DashboardContainer({ title, description, actions, children, className }: DashboardContainerProps) {
  return (
    <section className={cn("space-y-4", className)}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-white">{title}</h2>
          {description ? <p className="text-sm text-secondary/60">{description}</p> : null}
        </div>
        {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
      </div>
      <Card>{children}</Card>
    </section>
  );
}
