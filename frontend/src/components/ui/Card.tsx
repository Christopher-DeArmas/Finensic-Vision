import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export function Card({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return <div className={cn("card", className)}>{children}</div>;
}

/** A titled panel: header row (title + optional action) over a body. */
export function Panel({
  title,
  icon,
  action,
  className,
  bodyClassName,
  children,
}: {
  title: string;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
  bodyClassName?: string;
  children: ReactNode;
}) {
  return (
    <section className={cn("card flex flex-col", className)}>
      <header className="flex items-center justify-between gap-3 border-b border-white/5 px-5 py-3.5">
        <div className="flex items-center gap-2.5">
          {icon && <span className="text-gold-500">{icon}</span>}
          <h2 className="text-sm font-semibold tracking-tight text-white/90">
            {title}
          </h2>
        </div>
        {action}
      </header>
      <div className={cn("flex-1 p-5", bodyClassName)}>{children}</div>
    </section>
  );
}
