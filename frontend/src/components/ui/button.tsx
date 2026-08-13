"use client";

import type { ButtonHTMLAttributes, ReactNode, Ref } from "react";

import { useI18n } from "@/components/i18n/i18n-provider";
import { cn } from "@/utils/cn";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  ref?: Ref<HTMLButtonElement>;
  size?: "icon" | "md" | "sm";
  variant?: "danger" | "primary" | "secondary" | "tertiary";
};

const variants = {
  danger:
    "border border-rose-200/80 bg-rose-50/70 text-rose-700 shadow-sm hover:border-rose-300 hover:bg-rose-100/80 focus-visible:ring-rose-200 dark:border-rose-900/80 dark:bg-rose-950/35 dark:text-rose-300 dark:hover:bg-rose-950/60 dark:focus-visible:ring-rose-950",
  primary:
    "border border-indigo-500/40 bg-gradient-to-b from-indigo-500 to-indigo-600 text-white shadow-[0_7px_18px_rgba(79,70,229,.20),inset_0_1px_0_rgba(255,255,255,.25)] hover:-translate-y-px hover:from-indigo-500 hover:to-indigo-500 hover:shadow-[0_10px_24px_rgba(79,70,229,.28)] focus-visible:ring-indigo-200 disabled:translate-y-0 disabled:shadow-none dark:from-indigo-500 dark:to-indigo-600 dark:focus-visible:ring-indigo-950",
  secondary:
    "border border-slate-200/90 bg-white/80 text-slate-700 shadow-sm shadow-slate-950/[.03] hover:-translate-y-px hover:border-indigo-200 hover:bg-white hover:text-slate-950 focus-visible:ring-slate-200 dark:border-slate-700/80 dark:bg-slate-900/70 dark:text-slate-200 dark:hover:border-indigo-800 dark:hover:bg-slate-900 dark:hover:text-white dark:focus-visible:ring-slate-800",
  tertiary:
    "border border-transparent text-slate-600 hover:bg-slate-100/80 hover:text-slate-950 focus-visible:ring-slate-200 dark:text-slate-300 dark:hover:bg-slate-800/70 dark:hover:text-white dark:focus-visible:ring-slate-800",
} as const;

const sizes = {
  icon: "h-10 w-10 p-2",
  md: "min-h-10 px-4 py-2.5",
  sm: "min-h-9 px-3.5 py-2",
} as const;

export function Button({ children, className, ref, size = "md", type = "button", variant = "primary", ...props }: ButtonProps) {
  const { t } = useI18n();
  const localizedChildren: ReactNode = typeof children === "string" ? t(children) : children;
  return (
    <button
      className={cn(
        "inline-flex select-none items-center justify-center gap-2 rounded-xl text-sm font-semibold transition-[color,background-color,border-color,box-shadow,transform,opacity] duration-200 focus-visible:outline-none focus-visible:ring-4 disabled:cursor-not-allowed disabled:opacity-50",
        sizes[size], variants[variant], className,
      )}
      ref={ref}
      type={type}
      {...props}
    >
      {localizedChildren}
    </button>
  );
}
