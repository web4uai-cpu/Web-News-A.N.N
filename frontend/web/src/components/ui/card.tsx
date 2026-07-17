import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-edge bg-surface backdrop-blur",
        className
      )}
      {...props}
    />
  );
}

export function CardHeader({
  className,
  title,
  action,
  ...props
}: HTMLAttributes<HTMLDivElement> & { title?: ReactNode; action?: ReactNode }) {
  return (
    <div className={cn("flex items-center justify-between px-5 pt-5", className)} {...props}>
      {title !== undefined ? (
        <h3 className="text-sm font-semibold tracking-wide">{title}</h3>
      ) : (
        props.children
      )}
      {action}
    </div>
  );
}

export function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-5 py-4", className)} {...props} />;
}
