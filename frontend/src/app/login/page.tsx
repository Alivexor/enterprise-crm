"use client";

import { LanguageToggle } from "@/components/i18n/language-toggle";
import { useI18n } from "@/components/i18n/i18n-provider";
import { LoginForm } from "@/features/auth/login-form";

const productPoints = [
  "Customer 360 with relationship context",
  "Sales pipeline, planner and smart search",
  "Role-based access with complete audit trail",
] as const;

export default function LoginPage() {
  const { isRtl, t } = useI18n();
  return (
    <main className="relative min-h-dvh overflow-hidden bg-[#070b16] px-4 py-4 sm:px-6 sm:py-6">
      <div aria-hidden="true" className="absolute inset-0 bg-[radial-gradient(circle_at_10%_0%,rgba(99,102,241,.34),transparent_30rem),radial-gradient(circle_at_90%_100%,rgba(6,182,212,.15),transparent_28rem)]" />
      <div aria-hidden="true" className="absolute inset-0 opacity-[.08] [background-image:linear-gradient(rgba(255,255,255,.5)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.5)_1px,transparent_1px)] [background-size:44px_44px] [mask-image:linear-gradient(to_bottom,black,transparent_86%)]" />
      <div className={`absolute top-7 z-30 ${isRtl ? "left-7" : "right-7"}`}><LanguageToggle /></div>

      <section className="relative mx-auto grid min-h-[calc(100dvh-2rem)] max-w-[1260px] overflow-hidden rounded-[28px] border border-white/[.08] bg-white shadow-[0_36px_110px_rgba(0,0,0,.48)] dark:bg-slate-950 sm:min-h-[calc(100dvh-3rem)] lg:grid-cols-[1.08fr_.92fr]">
        <div className="relative hidden overflow-hidden bg-[#0b1020] p-10 text-white lg:flex lg:flex-col lg:justify-between xl:p-12">
          <div aria-hidden="true" className="absolute -right-24 -top-20 h-80 w-80 rounded-full bg-indigo-500/25 blur-3xl" />
          <div aria-hidden="true" className="absolute -bottom-36 -left-24 h-96 w-96 rounded-full bg-cyan-500/10 blur-3xl" />
          <div aria-hidden="true" className="absolute inset-0 opacity-[.045] [background-image:radial-gradient(white_1px,transparent_1px)] [background-size:15px_15px]" />

          <div className="relative flex items-center gap-3"><span className="relative flex h-11 w-11 items-center justify-center rounded-[14px] bg-gradient-to-br from-indigo-400 via-indigo-500 to-violet-700 text-base font-black shadow-[0_14px_36px_rgba(79,70,229,.40)] ring-1 ring-inset ring-white/20">E<span className="absolute inset-x-1 top-0 h-px bg-white/60" /></span><div><p className="font-bold tracking-[-.02em]">{t("Enterprise CRM")}</p><p className="mt-0.5 text-[11px] text-slate-400">{t("Revenue intelligence workspace")}</p></div></div>

          <div className="relative my-auto max-w-lg py-16">
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-400/20 bg-indigo-400/10 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[.16em] text-indigo-200"><span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,.8)]" />{t("Built for modern revenue teams")}</div>
            <h1 className="mt-7 text-[2.85rem] font-semibold leading-[1.08] tracking-[-.045em] text-white xl:text-[3.25rem]">{t("Every customer signal, one beautifully focused workspace.")}</h1>
            <p className="mt-6 max-w-md text-sm leading-7 text-slate-400">{t("Move from scattered follow-ups to a clear operating system for relationships, pipeline and execution.")}</p>
            <ul className="mt-9 grid gap-3">{productPoints.map((point) => <li className="group flex items-center gap-3 rounded-xl border border-white/[.06] bg-white/[.035] px-3.5 py-3 text-sm text-slate-200 transition hover:border-indigo-400/20 hover:bg-white/[.055]" key={point}><span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-indigo-400/10 text-indigo-300 ring-1 ring-inset ring-indigo-400/15"><svg aria-hidden="true" className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24"><path d="m6.5 12.5 3.2 3.2 7.8-8" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" /></svg></span>{t(point)}</li>)}</ul>
          </div>

          <div className="relative flex items-center justify-between text-[10px] text-slate-500"><span>{t("Secure sessions · audit ready · bilingual")}</span><span className="font-mono">CRM / 3.0</span></div>
        </div>

        <div className="relative flex items-center justify-center bg-gradient-to-b from-white to-slate-50/80 p-6 dark:from-slate-950 dark:to-[#090d16] sm:p-10 lg:p-14 xl:p-16">
          <div aria-hidden="true" className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-indigo-300/50 to-transparent lg:hidden" />
          <div className="w-full max-w-[420px]">
            <div className="mb-10 lg:hidden"><div className="flex h-11 w-11 items-center justify-center rounded-[14px] bg-gradient-to-br from-indigo-500 to-violet-700 text-sm font-black text-white shadow-lg shadow-indigo-500/20">E</div><p className="mt-4 text-sm font-bold text-slate-950 dark:text-white">{t("Enterprise CRM")}</p></div>
            <div className="crm-kicker">{t("Secure access")}</div>
            <h2 className="mt-5 text-3xl font-bold tracking-[-.04em] text-slate-950 dark:text-white sm:text-[2.15rem]">{t("Welcome back")}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-500 dark:text-slate-400">{t("Sign in to continue to your customer and revenue workspace.")}</p>
            <div className="mt-9"><LoginForm /></div>
            <div className="mt-8 flex items-center justify-center gap-2 text-[11px] text-slate-400"><svg aria-hidden="true" className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24"><rect height="10" rx="2" stroke="currentColor" strokeWidth="1.7" width="14" x="5" y="10"/><path d="M8 10V7a4 4 0 0 1 8 0v3" stroke="currentColor" strokeLinecap="round" strokeWidth="1.7"/></svg>{t("Protected by secure HttpOnly sessions")}</div>
          </div>
        </div>
      </section>
    </main>
  );
}
