"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast-provider";
import { V3Empty, V3Hero, V3Metric, V3Section } from "@/features/v3/v3-ui";
import { ApiError } from "@/services/api-client";
import { v3Service } from "@/services/v3-service";
import type { ApiKey, WebhookDelivery, WebhookEndpoint } from "@/types/v3";

function message(error: unknown) {
  return error instanceof ApiError ? error.message : "Unable to update developer settings.";
}

export function DeveloperWorkspace() {
  const { formatDateTime, formatNumber, t } = useI18n();
  const { notify } = useToast();
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [webhooks, setWebhooks] = useState<WebhookEndpoint[]>([]);
  const [deliveries, setDeliveries] = useState<WebhookDelivery[]>([]);
  const [keyName, setKeyName] = useState("");
  const [createdToken, setCreatedToken] = useState<string | null>(null);
  const [createdWebhookSecret, setCreatedWebhookSecret] = useState<string | null>(null);
  const [webhookName, setWebhookName] = useState("");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [events, setEvents] = useState("deal.created,deal.updated,lead.created,lead.updated");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const deliveredCount = useMemo(() => deliveries.filter((item) => item.status === "delivered").length, [deliveries]);
  const failedCount = useMemo(() => deliveries.filter((item) => item.status === "failed").length, [deliveries]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [nextKeys, nextWebhooks, nextDeliveries] = await Promise.all([
        v3Service.developer.apiKeys(),
        v3Service.developer.webhooks(),
        v3Service.developer.deliveries(),
      ]);
      setKeys(nextKeys);
      setWebhooks(nextWebhooks);
      setDeliveries(nextDeliveries);
    } catch (cause) {
      notify({ tone: "error", title: t("Unable to load developer platform"), description: t(message(cause)) });
    } finally {
      setLoading(false);
    }
  }, [notify, t]);

  useEffect(() => {
    void Promise.resolve().then(load);
  }, [load]);

  async function createKey(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      const created = await v3Service.developer.createApiKey(keyName.trim());
      setCreatedToken(created.token);
      setKeyName("");
      notify({ tone: "success", title: t("API key created"), description: t("Copy the token now. It is shown only once.") });
      await load();
    } catch (cause) {
      notify({ tone: "error", title: t("Unable to create API key"), description: t(message(cause)) });
    } finally {
      setSaving(false);
    }
  }

  async function revoke(key: ApiKey) {
    if (!window.confirm(t("Revoke this API key?"))) return;
    try {
      await v3Service.developer.revokeApiKey(key.id);
      await load();
    } catch (cause) {
      notify({ tone: "error", title: t("Unable to revoke API key"), description: t(message(cause)) });
    }
  }

  async function createWebhook(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      const created = await v3Service.developer.createWebhook({
        name: webhookName.trim(),
        url: webhookUrl.trim(),
        events: events.split(",").map((value) => value.trim()).filter(Boolean),
        is_active: true,
      });
      setCreatedWebhookSecret(created.signing_secret);
      setWebhookName("");
      setWebhookUrl("");
      notify({ tone: "success", title: t("Webhook endpoint registered"), description: t("Copy the signing secret now. It is shown only once.") });
      await load();
    } catch (cause) {
      notify({ tone: "error", title: t("Unable to register webhook"), description: t(message(cause)) });
    } finally {
      setSaving(false);
    }
  }

  async function retryDelivery(delivery: WebhookDelivery) {
    try {
      await v3Service.developer.retryDelivery(delivery.id);
      notify({ tone: "success", title: t("Webhook retry queued") });
      await load();
    } catch (cause) {
      notify({ tone: "error", title: t("Unable to retry webhook"), description: t(message(cause)) });
    }
  }

  return (
    <section className="crm-page mx-auto max-w-[1450px] space-y-6">
      <V3Hero
        accent="violet"
        eyebrow="V3 Platform"
        title="Developer platform"
        description="Use user-bound API keys and signed webhooks without paid integration middleware. Existing CRM roles and permissions remain the source of truth."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <V3Metric label="API keys" value={formatNumber(keys.length)} tone="violet" />
        <V3Metric label="Webhook endpoints" value={formatNumber(webhooks.length)} tone="cyan" />
        <V3Metric label="Delivered webhooks" value={formatNumber(deliveredCount)} tone="emerald" />
        <V3Metric label="Failed deliveries" value={formatNumber(failedCount)} tone="amber" />
      </div>

      {createdToken ? (
        <SecretCard
          label={t("Copy this API key now")}
          description={t("The secret token is never stored in plaintext and cannot be shown again.")}
          secret={createdToken}
          onCopied={() => notify({ tone: "success", title: t("Copied") })}
        />
      ) : null}

      {createdWebhookSecret ? (
        <SecretCard
          label={t("Copy this webhook signing secret now")}
          description={t("Use it to verify the X-CRM-Signature HMAC-SHA256 header. The CRM will not show this secret again.")}
          secret={createdWebhookSecret}
          onCopied={() => notify({ tone: "success", title: t("Copied") })}
        />
      ) : null}

      <div className="grid gap-6 xl:grid-cols-2">
        <V3Section title="Personal API keys" description="API keys authenticate as the user who created them, so existing roles and permissions still apply.">
          {loading ? <V3Empty><T>Loading API keys…</T></V3Empty> : keys.length ? (
            <div className="space-y-2">
              {keys.map((key) => (
                <div className="flex items-center gap-3 rounded-2xl border border-slate-200/70 px-4 py-3 dark:border-slate-800" key={key.id}>
                  <span className={`h-2 w-2 rounded-full ${key.is_active ? "bg-emerald-500" : "bg-slate-400"}`} />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-black text-slate-900 dark:text-white">{key.name}</p>
                    <p className="mt-0.5 font-mono text-[10px] text-slate-400" dir="ltr">crm_live_{key.prefix}_••••••••</p>
                    <p className="mt-1 text-[10px] text-slate-400">
                      <T>Created</T> {formatDateTime(key.created_at)}{key.last_used_at ? ` · ${t("Last used")} ${formatDateTime(key.last_used_at)}` : ""}
                    </p>
                  </div>
                  {key.is_active ? <Button onClick={() => void revoke(key)} size="sm" variant="danger">{t("Revoke")}</Button> : <span className="text-xs text-slate-400"><T>Revoked</T></span>}
                </div>
              ))}
            </div>
          ) : <V3Empty><T>No API keys yet.</T></V3Empty>}
          <form className="mt-5 flex gap-2" onSubmit={createKey}>
            <input className="crm-input flex-1" onChange={(event) => setKeyName(event.target.value)} placeholder={t("Integration name")} required value={keyName} />
            <Button disabled={saving || !keyName.trim()} type="submit">{t("Create key")}</Button>
          </form>
        </V3Section>

        <V3Section title="Webhook registry" description="Signed delivery uses your self-hosted worker, HTTPS and HMAC-SHA256; no paid middleware is required.">
          {webhooks.length ? (
            <div className="space-y-2">
              {webhooks.map((webhook) => (
                <div className="rounded-2xl border border-slate-200/70 p-4 dark:border-slate-800" key={webhook.id}>
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-black text-slate-900 dark:text-white">{webhook.name}</p>
                    <span className={`rounded-lg px-2 py-1 text-[10px] font-black ${webhook.is_active ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300" : "bg-slate-100 text-slate-500 dark:bg-slate-800"}`}><T>{webhook.is_active ? "Active" : "Inactive"}</T></span>
                  </div>
                  <p className="mt-2 truncate font-mono text-[10px] text-slate-400" dir="ltr">{webhook.url}</p>
                  <div className="mt-2 flex flex-wrap gap-1">{webhook.events.map((event) => <span className="rounded-lg bg-slate-100 px-2 py-1 text-[10px] text-slate-600 dark:bg-slate-800 dark:text-slate-300" key={event}>{event}</span>)}</div>
                  {webhook.last_error ? <p className="mt-2 text-xs text-rose-500"><T>Last error</T>: {webhook.last_error}</p> : null}
                </div>
              ))}
            </div>
          ) : <V3Empty><T>No webhook endpoints registered.</T></V3Empty>}
          <form className="mt-5 space-y-3" onSubmit={createWebhook}>
            <input className="crm-input w-full" onChange={(event) => setWebhookName(event.target.value)} placeholder={t("Webhook name")} required value={webhookName} />
            <input className="crm-input w-full" dir="ltr" onChange={(event) => setWebhookUrl(event.target.value)} placeholder="https://example.com/crm-hook" required type="url" value={webhookUrl} />
            <textarea className="crm-input min-h-24 w-full font-mono text-xs" dir="ltr" onChange={(event) => setEvents(event.target.value)} value={events} />
            <Button className="w-full" disabled={saving || !webhookName.trim() || !webhookUrl.trim()} type="submit">{t("Register webhook")}</Button>
          </form>
        </V3Section>
      </div>

      <V3Section title="Webhook delivery log" description="Inspect delivery status, HTTP responses and retry failed deliveries after fixing the receiver.">
        {loading ? <V3Empty><T>Loading webhook deliveries…</T></V3Empty> : deliveries.length ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[850px] text-sm">
              <thead className="text-[10px] uppercase tracking-[.1em] text-slate-400">
                <tr><th className="px-3 py-2 text-start"><T>Event</T></th><th className="px-3 py-2 text-start"><T>Status</T></th><th className="px-3 py-2 text-start"><T>Attempts</T></th><th className="px-3 py-2 text-start">HTTP</th><th className="px-3 py-2 text-start"><T>Created</T></th><th className="px-3 py-2 text-start"><T>Actions</T></th></tr>
              </thead>
              <tbody>
                {deliveries.slice(0, 100).map((delivery) => (
                  <tr className="border-t border-slate-100 dark:border-slate-800" key={delivery.id}>
                    <td className="px-3 py-3 font-mono text-xs" dir="ltr">{delivery.event_type}</td>
                    <td className="px-3 py-3"><T>{delivery.status}</T>{delivery.last_error ? <p className="mt-1 max-w-[360px] truncate text-[10px] text-rose-500" title={delivery.last_error}>{delivery.last_error}</p> : null}</td>
                    <td className="px-3 py-3">{formatNumber(delivery.attempts)}</td>
                    <td className="px-3 py-3 font-mono text-xs">{delivery.response_status ?? "—"}</td>
                    <td className="px-3 py-3 text-slate-500">{formatDateTime(delivery.created_at)}</td>
                    <td className="px-3 py-3">{delivery.status !== "delivered" ? <Button onClick={() => void retryDelivery(delivery)} size="sm" variant="secondary">{t("Retry")}</Button> : <span className="text-xs text-emerald-500"><T>Delivered</T></span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <V3Empty><T>No webhook deliveries yet.</T></V3Empty>}
      </V3Section>
    </section>
  );
}

function SecretCard({ label, description, secret, onCopied }: { label: string; description: string; secret: string; onCopied: () => void }) {
  const { t } = useI18n();
  return (
    <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 dark:border-amber-900 dark:bg-amber-950/30">
      <p className="text-sm font-black text-amber-900 dark:text-amber-100">{label}</p>
      <p className="mt-1 text-xs text-amber-700 dark:text-amber-300">{description}</p>
      <div className="mt-3 flex gap-2">
        <code className="min-w-0 flex-1 overflow-x-auto rounded-xl bg-slate-950 px-3 py-3 text-xs text-emerald-300" dir="ltr">{secret}</code>
        <Button onClick={() => { void navigator.clipboard.writeText(secret); onCopied(); }} variant="secondary">{t("Copy")}</Button>
      </div>
    </div>
  );
}
