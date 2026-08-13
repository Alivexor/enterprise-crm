"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import { useI18n } from "@/components/i18n/i18n-provider";

type ToastTone = "error" | "info" | "success" | "warning";
type ToastInput = { description?: string; duration?: number; title: string; tone?: ToastTone };
type ToastItem = ToastInput & { id: number; tone: ToastTone };
type ToastContextValue = {
  dismiss: (id: number) => void;
  notify: (toast: ToastInput) => number;
};

const ToastContext = createContext<ToastContextValue | null>(null);
let nextToastId = 1;

const toneClasses: Record<ToastTone, { dot: string; ring: string }> = {
  error: { dot: "bg-rose-500", ring: "ring-rose-500/15" },
  info: { dot: "bg-indigo-500", ring: "ring-indigo-500/15" },
  success: { dot: "bg-emerald-500", ring: "ring-emerald-500/15" },
  warning: { dot: "bg-amber-500", ring: "ring-amber-500/15" },
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const { t } = useI18n();
  const [items, setItems] = useState<ToastItem[]>([]);
  const timersRef = useRef<Map<number, number>>(new Map());

  const dismiss = useCallback((id: number) => {
    const timer = timersRef.current.get(id);
    if (timer !== undefined && typeof window !== "undefined") window.clearTimeout(timer);
    timersRef.current.delete(id);
    setItems((current) => current.filter((item) => item.id !== id));
  }, []);

  const notify = useCallback((input: ToastInput) => {
    const id = nextToastId++;
    const duration = Math.max(1200, input.duration ?? 4200);
    const item: ToastItem = { ...input, duration, id, tone: input.tone ?? "info" };
    setItems((current) => {
      const next = [...current, item];
      const overflow = next.slice(0, Math.max(0, next.length - 4));
      if (typeof window !== "undefined") {
        overflow.forEach((oldItem) => {
          const oldTimer = timersRef.current.get(oldItem.id);
          if (oldTimer !== undefined) window.clearTimeout(oldTimer);
          timersRef.current.delete(oldItem.id);
        });
      }
      return next.slice(-4);
    });
    if (typeof window !== "undefined") {
      const timer = window.setTimeout(() => dismiss(id), duration);
      timersRef.current.set(id, timer);
    }
    return id;
  }, [dismiss]);

  useEffect(() => () => {
    if (typeof window !== "undefined") {
      timersRef.current.forEach((timer) => window.clearTimeout(timer));
    }
    timersRef.current.clear();
  }, []);

  const value = useMemo(() => ({ dismiss, notify }), [dismiss, notify]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        aria-live="polite"
        aria-relevant="additions"
        className="pointer-events-none fixed inset-x-3 bottom-4 z-[100] flex flex-col items-end gap-2 sm:inset-x-auto sm:end-5 sm:w-[380px]"
      >
        {items.map((item) => {
          const tone = toneClasses[item.tone];
          return (
            <div
              aria-atomic="true"
              className={`pointer-events-auto crm-toast relative w-full overflow-hidden rounded-2xl border border-slate-200/80 bg-white/95 p-4 pb-5 shadow-[0_20px_60px_rgba(15,23,42,.18)] ring-4 ${tone.ring} backdrop-blur-xl dark:border-slate-700/80 dark:bg-slate-900/95`}
              key={item.id}
              role={item.tone === "error" ? "alert" : "status"}
            >
              <div className="flex items-start gap-3">
                <span className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ${tone.dot} shadow-[0_0_0_4px_rgba(148,163,184,.10)]`} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-bold text-slate-950 dark:text-white">{item.title}</p>
                  {item.description ? <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">{item.description}</p> : null}
                </div>
                <button
                  aria-label={t("Dismiss notification")}
                  className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
                  onClick={() => dismiss(item.id)}
                  type="button"
                >
                  <svg aria-hidden="true" className="h-3.5 w-3.5" fill="none" viewBox="0 0 20 20"><path d="m6 6 8 8m0-8-8 8" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" /></svg>
                </button>
              </div>
              <span className="crm-toast-progress" aria-hidden="true">
                <span className="crm-toast-progress-bar" style={{ animationDuration: `${item.duration ?? 4200}ms` }} />
              </span>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const value = useContext(ToastContext);
  if (!value) throw new Error("useToast must be used inside ToastProvider");
  return value;
}
