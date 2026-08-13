"use client";

import { FormEvent, useState } from "react";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast-provider";
import { SettingsNavigation } from "@/features/settings/settings-navigation";
import { V3Hero, V3Section } from "@/features/v3/v3-ui";
import { useAuth } from "@/hooks/use-auth";
import { apiClient, ApiError } from "@/services/api-client";

type SetupResponse = { secret: string; otpauth_uri: string };
type ConfirmResponse = { enabled: boolean; recovery_codes: string[] };

function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to update multi-factor authentication.";
}

export function SecurityWorkspace() {
  const { t } = useI18n();
  const { notify } = useToast();
  const { refreshUser, user } = useAuth();
  const [setup, setSetup] = useState<SetupResponse | null>(null);
  const [setupCode, setSetupCode] = useState("");
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const [disablePassword, setDisablePassword] = useState("");
  const [disableCode, setDisableCode] = useState("");
  const [busy, setBusy] = useState(false);

  async function beginSetup() {
    setBusy(true);
    try {
      const response = await apiClient.post<SetupResponse>("/auth/mfa/setup");
      setSetup(response);
      setRecoveryCodes([]);
      notify({ tone: "success", title: t("MFA setup started"), description: t("Add the secret to your authenticator app, then enter the current six-digit code.") });
    } catch (cause) {
      notify({ tone: "error", title: t("Unable to start MFA setup"), description: t(errorMessage(cause)) });
    } finally { setBusy(false); }
  }

  async function confirm(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      const response = await apiClient.post<ConfirmResponse>("/auth/mfa/confirm", JSON.stringify({ code: setupCode }));
      setRecoveryCodes(response.recovery_codes);
      setSetup(null);
      setSetupCode("");
      await refreshUser();
      notify({ tone: "success", title: t("MFA enabled"), description: t("Future sign-ins now require a second factor.") });
    } catch (cause) {
      notify({ tone: "error", title: t("Unable to confirm MFA"), description: t(errorMessage(cause)) });
    } finally { setBusy(false); }
  }

  async function disable(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      await apiClient.post<void>("/auth/mfa/disable", JSON.stringify({ password: disablePassword, code: disableCode }));
      setDisablePassword(""); setDisableCode(""); setRecoveryCodes([]); setSetup(null);
      await refreshUser();
      notify({ tone: "success", title: t("MFA disabled") });
    } catch (cause) {
      notify({ tone: "error", title: t("Unable to disable MFA"), description: t(errorMessage(cause)) });
    } finally { setBusy(false); }
  }

  return (
    <section className="crm-page mx-auto max-w-[1380px] space-y-6">
      <V3Hero accent="violet" eyebrow="V3 Security" title="Security center" description="Protect your account with standards-based time-based one-time passwords and recovery codes. No paid identity provider is required." />
      <SettingsNavigation compact />
      <div className="grid gap-6 xl:grid-cols-[1.05fr_.95fr]">
        <V3Section title="Multi-factor authentication" description="Use any authenticator that supports standard TOTP codes.">
          <div className="rounded-2xl border border-slate-200/75 bg-slate-50/70 p-4 dark:border-slate-800 dark:bg-slate-900/45">
            <div className="flex items-center justify-between gap-3">
              <div><p className="text-sm font-black text-slate-950 dark:text-white"><T>Authenticator app</T></p><p className="mt-1 text-xs text-slate-500"><T>{user?.mfa_enabled ? "MFA is enabled for this account." : "MFA is currently disabled."}</T></p></div>
              <span className={`rounded-xl px-3 py-1.5 text-[11px] font-black ${user?.mfa_enabled ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300" : "bg-slate-200/70 text-slate-600 dark:bg-slate-800 dark:text-slate-300"}`}><T>{user?.mfa_enabled ? "Enabled" : "Disabled"}</T></span>
            </div>
          </div>

          {!user?.mfa_enabled ? <div className="mt-4 space-y-4">
            {!setup ? <Button disabled={busy} onClick={() => void beginSetup()}>{busy ? "Preparing…" : "Enable MFA"}</Button> : <form className="space-y-4" onSubmit={confirm}>
              <div className="rounded-2xl border border-indigo-200 bg-indigo-50/60 p-4 dark:border-indigo-900 dark:bg-indigo-950/25">
                <p className="text-xs font-bold text-indigo-700 dark:text-indigo-300"><T>Authenticator secret</T></p>
                <code className="mt-2 block overflow-x-auto rounded-xl bg-slate-950 px-3 py-3 text-xs text-emerald-300" dir="ltr">{setup.secret}</code>
                <p className="mt-3 text-[11px] leading-5 text-slate-500"><T>Scan support is not required: copy this secret into Google Authenticator, Microsoft Authenticator, 2FAS, Aegis or another TOTP-compatible app.</T></p>
              </div>
              <label className="block text-xs font-bold text-slate-600 dark:text-slate-300"><T>Six-digit code</T><input autoComplete="one-time-code" className="crm-input mt-2 w-full" dir="ltr" inputMode="numeric" maxLength={6} onChange={(event) => setSetupCode(event.target.value.replace(/\D/g, ""))} required value={setupCode} /></label>
              <Button disabled={busy || setupCode.length !== 6} type="submit">{t("Confirm and enable")}</Button>
            </form>}
          </div> : <form className="mt-4 space-y-3" onSubmit={disable}>
            <p className="text-xs leading-5 text-slate-500"><T>Disabling MFA requires your password and either a current authenticator code or an unused recovery code.</T></p>
            <input autoComplete="current-password" className="crm-input w-full" onChange={(event) => setDisablePassword(event.target.value)} placeholder={t("Current password")} required type="password" value={disablePassword} />
            <input autoComplete="one-time-code" className="crm-input w-full" dir="ltr" onChange={(event) => setDisableCode(event.target.value)} placeholder={t("Authenticator or recovery code")} required value={disableCode} />
            <Button disabled={busy} type="submit" variant="danger">{t("Disable MFA")}</Button>
          </form>}
        </V3Section>

        <V3Section title="Recovery codes" description="Recovery codes are generated once when MFA is enabled. Store them somewhere safe outside the CRM.">
          {recoveryCodes.length ? <div><div className="grid gap-2 sm:grid-cols-2">{recoveryCodes.map((code) => <code className="rounded-xl border border-slate-200 bg-slate-950 px-3 py-2.5 text-center text-xs text-emerald-300 dark:border-slate-800" dir="ltr" key={code}>{code}</code>)}</div><Button className="mt-4" onClick={() => void navigator.clipboard.writeText(recoveryCodes.join("\n"))} variant="secondary">{t("Copy recovery codes")}</Button></div> : <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50/60 px-5 py-8 text-center text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900/40"><T>Recovery codes will appear here immediately after MFA is enabled.</T></div>}
        </V3Section>
      </div>
    </section>
  );
}
