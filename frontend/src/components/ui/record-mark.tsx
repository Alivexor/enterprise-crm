import { cn } from "@/utils/cn";

type RecordMarkTone = "amber" | "cyan" | "emerald" | "indigo" | "rose" | "slate" | "violet";

const tones: Record<RecordMarkTone, string> = {
  amber: "from-amber-100 to-orange-50 text-amber-700 ring-amber-200/70 dark:from-amber-950/70 dark:to-orange-950/30 dark:text-amber-300 dark:ring-amber-900/70",
  cyan: "from-cyan-100 to-sky-50 text-cyan-700 ring-cyan-200/70 dark:from-cyan-950/70 dark:to-sky-950/30 dark:text-cyan-300 dark:ring-cyan-900/70",
  emerald: "from-emerald-100 to-teal-50 text-emerald-700 ring-emerald-200/70 dark:from-emerald-950/70 dark:to-teal-950/30 dark:text-emerald-300 dark:ring-emerald-900/70",
  indigo: "from-indigo-100 to-violet-50 text-indigo-700 ring-indigo-200/70 dark:from-indigo-950/70 dark:to-violet-950/30 dark:text-indigo-300 dark:ring-indigo-900/70",
  rose: "from-rose-100 to-pink-50 text-rose-700 ring-rose-200/70 dark:from-rose-950/70 dark:to-pink-950/30 dark:text-rose-300 dark:ring-rose-900/70",
  slate: "from-slate-100 to-slate-50 text-slate-700 ring-slate-200/80 dark:from-slate-800 dark:to-slate-900 dark:text-slate-200 dark:ring-slate-700/80",
  violet: "from-violet-100 to-fuchsia-50 text-violet-700 ring-violet-200/70 dark:from-violet-950/70 dark:to-fuchsia-950/30 dark:text-violet-300 dark:ring-violet-900/70",
};

function initials(label: string): string {
  const words = label.trim().split(/\s+/).filter(Boolean).slice(0, 2);
  const value = words.map((word) => Array.from(word)[0] ?? "").join("");
  return value || "•";
}

export function RecordMark({ className, label, tone = "indigo" }: { className?: string; label: string; tone?: RecordMarkTone }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br text-[11px] font-extrabold uppercase shadow-[inset_0_1px_0_rgba(255,255,255,.55)] ring-1 ring-inset",
        tones[tone],
        className,
      )}
    >
      {initials(label)}
    </span>
  );
}
