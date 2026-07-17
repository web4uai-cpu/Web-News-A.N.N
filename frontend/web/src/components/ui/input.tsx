"use client";

import { forwardRef, useId, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, error, className, id, ...props },
  ref
) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const errorId = `${inputId}-error`;
  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="mb-1 block text-xs text-muted">
          {label}
        </label>
      )}
      <input
        ref={ref}
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={cn(
          "w-full rounded-lg border border-edge-strong bg-surface px-3 py-2 text-sm text-foreground",
          "placeholder:text-muted/60 outline-none focus:border-indigo-500/50",
          error && "border-rose-500/60",
          className
        )}
        {...props}
      />
      {error && (
        <p id={errorId} role="alert" className="mt-1 text-xs text-rose-400">
          {error}
        </p>
      )}
    </div>
  );
});
