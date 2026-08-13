"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/services/api-client";

export function LoginForm() {
  const router = useRouter();
  const { t } = useI18n();
  const { isLoading: isRestoringSession, signIn, user } = useAuth();
  const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [mfaCode, setMfaCode] = useState(""); const [mfaRequired, setMfaRequired] = useState(false);
  const [error, setError] = useState<string | null>(null); const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => { if (!isRestoringSession && user !== null) router.replace("/dashboard"); }, [isRestoringSession, router, user]);
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(null); setIsSubmitting(true);
    try { await signIn({ email, password, ...(mfaRequired ? { mfa_code: mfaCode } : {}) }); router.replace("/dashboard"); }
    catch (caughtError) {
      if (caughtError instanceof ApiError && caughtError.status === 401 && caughtError.message === "MFA code required") {
        setMfaRequired(true); setMfaCode(""); setError(null);
      } else {
        setError(caughtError instanceof ApiError ? caughtError.message : t("Unable to sign in. Please try again."));
      }
    }
    finally { setIsSubmitting(false); }
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      <div className="space-y-2"><label className="text-xs font-bold text-slate-700 dark:text-slate-300" htmlFor="email">{t("Email address")}</label><div className="relative"><svg aria-hidden="true" className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 rtl:left-auto rtl:right-3.5" fill="none" viewBox="0 0 24 24"><rect height="14" rx="2" stroke="currentColor" strokeWidth="1.6" width="18" x="3" y="5"/><path d="m4.5 7 7.5 6 7.5-6" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.6"/></svg><input autoComplete="email" className="crm-input w-full py-3 pe-3.5 ps-10 text-sm" id="email" name="email" onChange={(event) => setEmail(event.target.value)} placeholder="you@company.com" required type="email" value={email} /></div></div>
      <div className="space-y-2"><label className="text-xs font-bold text-slate-700 dark:text-slate-300" htmlFor="password">{t("Password")}</label><div className="relative"><svg aria-hidden="true" className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 rtl:left-auto rtl:right-3.5" fill="none" viewBox="0 0 24 24"><rect height="10" rx="2" stroke="currentColor" strokeWidth="1.6" width="16" x="4" y="10"/><path d="M7 10V7a5 5 0 0 1 10 0v3" stroke="currentColor" strokeLinecap="round" strokeWidth="1.6"/></svg><input autoComplete="current-password" className="crm-input w-full py-3 pe-3.5 ps-10 text-sm" id="password" name="password" onChange={(event) => setPassword(event.target.value)} required type="password" value={password} /></div></div>
      {mfaRequired ? <div className="space-y-2"><label className="text-xs font-bold text-slate-700 dark:text-slate-300" htmlFor="mfa-code">{t("Authenticator code")}</label><input autoComplete="one-time-code" autoFocus className="crm-input w-full py-3 text-center font-mono text-lg tracking-[.35em]" dir="ltr" id="mfa-code" inputMode="text" maxLength={64} onChange={(event) => setMfaCode(event.target.value)} placeholder="000000 / recovery code" required value={mfaCode} /><p className="text-[11px] leading-5 text-slate-500">{t("Enter the six-digit code from your authenticator app or use a recovery code.")}</p></div> : null}
      {error ? <p className="rounded-xl border border-rose-200/80 bg-rose-50 px-3.5 py-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-200" role="alert"><T>{error}</T></p> : null}
      <button className="group relative flex min-h-11 w-full items-center justify-center overflow-hidden rounded-xl border border-indigo-500/40 bg-gradient-to-b from-indigo-500 to-indigo-600 px-4 py-3 text-sm font-bold text-white shadow-[0_10px_28px_rgba(79,70,229,.24),inset_0_1px_0_rgba(255,255,255,.22)] transition-[background-color,border-color,box-shadow,transform,opacity] duration-200 hover:-translate-y-px hover:shadow-[0_14px_32px_rgba(79,70,229,.32)] focus:outline-none focus:ring-4 focus:ring-indigo-200 disabled:translate-y-0 disabled:cursor-not-allowed disabled:opacity-60 dark:focus:ring-indigo-950" disabled={isSubmitting || isRestoringSession || (mfaRequired && mfaCode.length < 6)} type="submit"><span className="relative z-10">{isSubmitting ? t("Signing in…") : t("Sign in")}</span><span aria-hidden="true" className="absolute inset-y-0 -left-1/3 w-1/3 skew-x-[-18deg] bg-white/15 blur-sm transition-transform duration-500 group-hover:translate-x-[430%]" /></button>
    </form>
  );
}
