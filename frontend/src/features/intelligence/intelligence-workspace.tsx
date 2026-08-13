"use client";

import Link from "next/link";
import { type FormEvent, type ReactNode, useCallback, useEffect, useMemo, useState } from "react";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast-provider";
import { V3Empty, V3Hero, V3Metric, V3Section } from "@/features/v3/v3-ui";
import { ApiError } from "@/services/api-client";
import { v3Service } from "@/services/v3-service";
import type { AiModel, AiStatus, DataQuality, MorningBrief, ReportBuilderResult, RevenueForecast, WinLossAnalytics } from "@/types/v3";

function message(error: unknown): string { return error instanceof ApiError ? error.message : "Unable to load V3 intelligence data."; }

function severityClass(severity: "low" | "medium" | "high"): string {
  return severity === "high" ? "bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300" : severity === "medium" ? "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300" : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300";
}

function modelSize(sizeBytes: number | null): string | null {
  if (!sizeBytes) return null;
  const gigabytes = sizeBytes / 1024 ** 3;
  return gigabytes >= 1 ? `${gigabytes.toFixed(1)} GB` : `${Math.round(sizeBytes / 1024 ** 2)} MB`;
}

/** Render the small, predictable Markdown subset returned by the local copilot without injecting HTML. */
function inlineMarkdown(value: string): ReactNode[] {
  return value.split(/(\*\*[^*\n]+\*\*|`[^`\n]+`)/g).filter(Boolean).map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={index}>{part.slice(2, -2)}</strong>;
    if (part.startsWith("`") && part.endsWith("`")) return <code key={index} className="rounded bg-slate-900/10 px-1 py-0.5 font-mono text-[0.85em] dark:bg-white/10">{part.slice(1, -1)}</code>;
    return <span key={index}>{part}</span>;
  });
}

function CopilotAnswer({ value }: { value: string }) {
  return <div className="space-y-3">
    {value.trim().split(/\n{2,}/).filter(Boolean).map((block, blockIndex) => {
      const lines = block.split("\n").filter(Boolean);
      const bulletList = lines.every((line) => /^\s*[-*]\s+/.test(line));
      const numberedList = lines.every((line) => /^\s*\d+[.)]\s+/.test(line));
      if (bulletList || numberedList) {
        const List = numberedList ? "ol" : "ul";
        const marker = numberedList ? /^\s*\d+[.)]\s+/ : /^\s*[-*]\s+/;
        return <List key={blockIndex} className={numberedList ? "list-decimal space-y-1 ps-5" : "list-disc space-y-1 ps-5"}>{lines.map((line, lineIndex) => <li key={lineIndex}>{inlineMarkdown(line.replace(marker, ""))}</li>)}</List>;
      }
      const heading = lines.length === 1 && /^#{1,3}\s+/.test(lines[0]);
      if (heading) return <h4 key={blockIndex} className="font-semibold text-slate-900 dark:text-white">{inlineMarkdown(lines[0].replace(/^#{1,3}\s+/, ""))}</h4>;
      return <p key={blockIndex}>{lines.map((line, lineIndex) => <span key={lineIndex}>{inlineMarkdown(line)}{lineIndex < lines.length - 1 ? <br /> : null}</span>)}</p>;
    })}
  </div>;
}

async function readCopilotStream(response: Response, onToken: (token: string) => void, onProgress?: (status: string) => void): Promise<void> {
  if (!response.body) throw new Error("Streaming is not supported by this browser.");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffered = "";
  while (true) {
    const { done, value } = await reader.read();
    buffered += decoder.decode(value ?? new Uint8Array(), { stream: !done });
    const events = buffered.split("\n\n");
    buffered = events.pop() ?? "";
    for (const event of events) {
      const data = event.split("\n").find((line) => line.startsWith("data: "))?.slice(6);
      if (!data) continue;
      const message = JSON.parse(data) as { type?: string; text?: string; detail?: string };
      if (message.type === "token" && typeof message.text === "string") onToken(message.text);
      if (message.type === "progress") onProgress?.(message.detail ?? "Downloading model…");
      if (message.type === "error") throw new Error(message.detail ?? "Local AI streaming failed.");
    }
    if (done) return;
  }
}

export function IntelligenceWorkspace() {
  const { formatMoney, formatNumber, locale, t } = useI18n();
  const { notify } = useToast();
  const [quality, setQuality] = useState<DataQuality | null>(null);
  const [forecast, setForecast] = useState<RevenueForecast | null>(null);
  const [ai, setAi] = useState<AiStatus | null>(null);
  const [brief, setBrief] = useState<MorningBrief | null>(null);
  const [winLoss, setWinLoss] = useState<WinLossAnalytics | null>(null);
  const [prompt, setPrompt] = useState("");
  const [answer, setAnswer] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [pullingModel, setPullingModel] = useState<string | null>(null);
  const [pullProgress, setPullProgress] = useState("");
  const [reportResource, setReportResource] = useState("deals");
  const [reportMetric, setReportMetric] = useState("count");
  const [reportGroupBy, setReportGroupBy] = useState("status");
  const [report, setReport] = useState<ReportBuilderResult | null>(null);
  const [reporting, setReporting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    const [qualityResult, forecastResult, aiResult, briefResult, winLossResult] = await Promise.allSettled([
      v3Service.intelligence.dataQuality(),
      v3Service.intelligence.forecast(),
      v3Service.ai.status(),
      v3Service.intelligence.morningBrief(),
      v3Service.intelligence.winLoss(),
    ]);
    if (qualityResult.status === "fulfilled") setQuality(qualityResult.value);
    if (forecastResult.status === "fulfilled") setForecast(forecastResult.value);
    if (aiResult.status === "fulfilled") setAi(aiResult.value);
    if (briefResult.status === "fulfilled") setBrief(briefResult.value);
    if (winLossResult.status === "fulfilled") setWinLoss(winLossResult.value);
    const rejected = [qualityResult, forecastResult, aiResult, briefResult, winLossResult].find((item) => item.status === "rejected");
    setError(rejected?.status === "rejected" ? message(rejected.reason) : null);
    setLoading(false);
  }, []);

  useEffect(() => { void Promise.resolve().then(load); }, [load]);

  async function runReport() {
    setReporting(true);
    try { setReport(await v3Service.intelligence.report(reportResource, reportMetric, reportGroupBy)); }
    catch (cause) { notify({ tone: "error", title: t("Unable to build report"), description: t(message(cause)) }); }
    finally { setReporting(false); }
  }

  async function ask(event: FormEvent) {
    event.preventDefault();
    if (prompt.trim().length < 2 || asking) return;
    setAsking(true);
    setAnswer("");
    try {
      const response = await v3Service.ai.streamCopilot(prompt.trim(), locale, selectedModel || undefined);
      await readCopilotStream(response, (token) => setAnswer((current) => current + token));
    } catch (cause) {
      notify({ tone: "error", title: t("Copilot request failed"), description: t(message(cause)) });
    } finally { setAsking(false); }
  }

  const currency = forecast?.currency ?? "USD";
  const money = (value: string | number) => formatMoney(value, currency);
  const qualityTone = useMemo(() => quality && quality.score >= 90 ? "emerald" : quality && quality.score >= 70 ? "amber" : "rose", [quality]) as "emerald" | "amber" | "rose";
  const models = ai ? [...ai.installed_models, ...ai.recommended_models.filter((candidate) => !ai.installed_models.some((installed) => installed.name === candidate.name))] : [];

  async function copyInstallCommand(model: AiModel) {
    const command = `ollama pull ${model.name}`;
    try {
      await navigator.clipboard.writeText(command);
      notify({ tone: "success", title: "Install command copied", description: command });
    } catch {
      notify({ tone: "info", title: "Install this model", description: command });
    }
  }

  async function pullModel(model: AiModel) {
    if (!window.confirm(`Download ${model.name}? This can use several GB of disk space and bandwidth.`)) return;
    setPullingModel(model.name); setPullProgress("Starting download…");
    try {
      const response = await v3Service.ai.pullModel(model.name);
      await readCopilotStream(response, () => {}, setPullProgress);
      setPullProgress("Download completed. Refreshing models…");
      await load(); setSelectedModel(model.name);
    } catch (cause) { notify({ tone: "error", title: "Model download failed", description: cause instanceof Error ? cause.message : "Please try again." }); }
    finally { setPullingModel(null); }
  }

  return (
    <section className="crm-page mx-auto max-w-[1500px] space-y-6">
      <V3Hero
        accent="violet"
        eyebrow="V3 Intelligence"
        title="Revenue intelligence center"
        description="Local-first AI, pipeline forecasting, relationship signals and data quality in one operating view — without a paid AI API."
        actions={<Button onClick={() => void load()} variant="secondary"><T>Refresh intelligence</T></Button>}
      />

      {error ? <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">{t(error)}</div> : null}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <V3Metric label="CRM data health" value={loading || !quality ? "—" : `${formatNumber(quality.score)}%`} hint="Duplicate, stale and incomplete records" tone={qualityTone} />
        <V3Metric label="Open pipeline" value={loading || !forecast ? "—" : money(forecast.open_pipeline)} hint="Total value of open opportunities" tone="indigo" />
        <V3Metric label="Weighted pipeline" value={loading || !forecast ? "—" : money(forecast.weighted_pipeline)} hint="Probability-adjusted pipeline value" tone="cyan" />
        <V3Metric label="Won revenue" value={loading || !forecast ? "—" : money(forecast.won_revenue)} hint="Closed-won revenue in CRM" tone="emerald" />
      </div>

      <V3Section title="Morning command brief" description="A zero-cost action queue computed from your own CRM data before any AI model is involved.">
        {!brief ? <V3Empty><T>No personal brief is available yet.</T></V3Empty> : (
          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <MiniMetric label="Overdue tasks" value={formatNumber(brief.overdue_tasks)} tone="rose" />
              <MiniMetric label="Due today" value={formatNumber(brief.due_today)} tone="amber" />
              <MiniMetric label="Stale leads" value={formatNumber(brief.stale_leads)} tone="violet" />
              <MiniMetric label="Deals closing soon" value={formatNumber(brief.closing_soon_deals)} tone="cyan" />
            </div>
            {brief.actions.length ? <div className="grid gap-2 lg:grid-cols-2">{brief.actions.slice(0, 10).map((item) => <Link className="group flex items-center gap-3 rounded-2xl border border-slate-200/70 bg-white/70 px-4 py-3 transition-[border-color,background-color,transform] hover:-translate-y-px hover:border-indigo-200 dark:border-slate-800 dark:bg-slate-950/60 dark:hover:border-indigo-900" href={item.route} key={`${item.kind}-${item.entity_id}`}><span className={`h-2.5 w-2.5 shrink-0 rounded-full ${item.priority === "high" ? "bg-rose-500" : item.priority === "medium" ? "bg-amber-500" : "bg-slate-400"}`} /><div className="min-w-0 flex-1"><p className="truncate text-sm font-black text-slate-900 dark:text-white">{item.title}</p><p className="mt-0.5 truncate text-xs text-slate-500"><T>{item.reason}</T></p></div><span className="text-slate-300 transition-transform group-hover:translate-x-0.5 rtl:group-hover:-translate-x-0.5">→</span></Link>)}</div> : <V3Empty><T>Nothing urgent needs your attention.</T></V3Empty>}
          </div>
        )}
      </V3Section>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_.95fr]">
        <V3Section title="Local AI copilot" description="Ask questions about your CRM. Processing stays on your configured local Ollama instance.">
          <div className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3 dark:border-slate-800 dark:bg-slate-900/60">
            <span className={`h-2.5 w-2.5 rounded-full ${ai?.available ? "bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,.55)]" : "bg-slate-400"}`} />
            <div className="min-w-0 flex-1"><p className="text-sm font-bold text-slate-900 dark:text-white"><T>{ai?.available ? "Local AI online" : "Local AI offline"}</T></p><p className="mt-0.5 truncate text-xs text-slate-500" data-bidi="ltr">{ai?.model ?? "Ollama"} · {ai?.detail ?? t("Checking local AI…")}</p></div>
          </div>
          {!ai?.ollama_reachable ? <div className="mt-3 rounded-2xl border border-amber-200 bg-amber-50/70 p-4 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/25 dark:text-amber-100"><p className="font-black">Set up Ollama</p><ol className="mt-2 list-decimal space-y-1.5 pl-5 text-xs leading-5"><li>Install Ollama: <a className="font-bold underline" href="https://ollama.com/download" rel="noreferrer" target="_blank">ollama.com/download</a></li><li>Start the Ollama application or run <code className="rounded bg-black/5 px-1 py-0.5 dark:bg-white/10">ollama serve</code>.</li><li>Install the configured model: <code className="rounded bg-black/5 px-1 py-0.5 dark:bg-white/10">ollama pull {ai?.model ?? "gemma3:4b"}</code>.</li><li>Use Refresh intelligence after the model finishes downloading.</li></ol></div> : null}
          {ai?.ollama_reachable ? <div className="mt-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950/35"><div className="flex items-center justify-between gap-3"><div><p className="text-sm font-black text-slate-900 dark:text-white">Local models</p><p className="mt-0.5 text-xs text-slate-500">Installed models are ready to use. Copy a command for a suggested model that is missing.</p></div><span className="text-xs font-bold text-slate-400">{ai.installed_models.length} installed</span></div><div className="mt-3 grid gap-2 sm:grid-cols-2">{models.map((model) => <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2.5 dark:bg-slate-900" key={model.name}><div className="min-w-0"><p className="truncate text-xs font-bold text-slate-800 dark:text-slate-100">{model.name}{model.name === ai.model ? <span className="ml-1.5 text-[10px] text-violet-600 dark:text-violet-300">configured</span> : null}</p><p className={`mt-0.5 text-[10px] font-bold ${model.installed ? "text-emerald-600 dark:text-emerald-300" : "text-amber-600 dark:text-amber-300"}`}>{model.installed ? "Installed" : "Not installed"}{modelSize(model.size_bytes) ? ` · ${modelSize(model.size_bytes)}` : ""}</p></div>{!model.installed ? <Button onClick={() => void copyInstallCommand(model)} size="sm" variant="secondary">Copy install</Button> : null}</div>)}</div></div> : null}
          {ai?.ollama_reachable && ai.installed_models.length ? <div className="mt-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950/35"><label className="block text-xs font-bold text-slate-500">Active model<select className="crm-select mt-1.5 w-full" onChange={(event) => setSelectedModel(event.target.value)} value={selectedModel || ai.model}>{ai.installed_models.map((model) => <option key={model.name} value={model.name}>{model.name}</option>)}</select></label><div className="mt-3 grid gap-2 sm:grid-cols-2">{models.filter((model) => !model.installed).map((model) => <div className="flex items-center justify-between gap-2 rounded-xl bg-slate-50 px-3 py-2.5 dark:bg-slate-900" key={model.name}><span className="text-xs font-bold">{model.name}</span><Button disabled={pullingModel !== null} onClick={() => void pullModel(model)} size="sm">{pullingModel === model.name ? "Downloading…" : "Download"}</Button></div>)}</div>{pullProgress ? <p className="mt-3 text-xs font-bold text-violet-600">{pullProgress}</p> : null}</div> : null}
          <form className="mt-4" onSubmit={ask}>
            <textarea className="crm-input min-h-28 w-full resize-y" onChange={(e) => setPrompt(e.target.value)} placeholder={t("Example: Which open deals need attention this week?")} value={prompt} />
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3"><p className="text-xs text-slate-400"><T>Read-only CRM context is sent only to your local Ollama server.</T></p><Button disabled={!ai?.available || asking || prompt.trim().length < 2} type="submit">{asking ? t("Thinking…") : t("Ask copilot")}</Button></div>
          </form>
          {answer || asking ? <div className="mt-5 rounded-2xl border border-violet-200/70 bg-violet-50/60 p-5 text-sm leading-7 text-slate-700 dark:border-violet-900/70 dark:bg-violet-950/25 dark:text-slate-200"><CopilotAnswer value={answer} />{asking ? <span className="ml-1 inline-block h-4 w-1 animate-pulse bg-violet-500 align-middle" aria-label="Streaming response" /> : null}</div> : null}
        </V3Section>

        <V3Section title="Data quality center" description="A continuously computed health check for records that can weaken sales execution.">
          {!quality?.issues.length ? <V3Empty><T>Your CRM data is looking clean.</T></V3Empty> : (
            <div className="space-y-2.5">
              {quality.issues.map((issue) => <div className="flex items-center gap-3 rounded-2xl border border-slate-200/70 bg-slate-50/60 px-4 py-3 dark:border-slate-800 dark:bg-slate-900/45" key={issue.code}><span className={`rounded-lg px-2 py-1 text-[10px] font-black uppercase ${severityClass(issue.severity)}`}><T>{issue.severity}</T></span><div className="min-w-0 flex-1"><p className="text-sm font-bold text-slate-900 dark:text-white"><T>{issue.title}</T></p><p className="mt-0.5 text-xs text-slate-500"><T>{issue.resource}</T></p></div><span className="text-lg font-black tabular-nums text-slate-950 dark:text-white">{formatNumber(issue.count)}</span></div>)}
            </div>
          )}
        </V3Section>
      </div>

      <V3Section title="Forecast scenarios" description="Deterministic revenue scenarios derived from live deal value and probability — no AI required.">
        {!forecast ? <V3Empty><T>No forecast data is available yet.</T></V3Empty> : <>
          <div className="grid gap-3 sm:grid-cols-3"><div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-900/55"><p className="text-xs font-bold text-slate-400"><T>Commit</T></p><p className="mt-2 text-xl font-black text-slate-950 dark:text-white">{money(forecast.commit)}</p></div><div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-900/55"><p className="text-xs font-bold text-slate-400"><T>Best case</T></p><p className="mt-2 text-xl font-black text-slate-950 dark:text-white">{money(forecast.best_case)}</p></div><div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-900/55"><p className="text-xs font-bold text-slate-400"><T>Pipeline</T></p><p className="mt-2 text-xl font-black text-slate-950 dark:text-white">{money(forecast.pipeline)}</p></div></div>
          <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">{forecast.buckets.map((bucket) => <div className="rounded-2xl border border-slate-200/70 p-4 dark:border-slate-800" key={bucket.label}><div className="flex items-center justify-between gap-3"><p className="text-sm font-bold text-slate-900 dark:text-white"><T>{bucket.label}</T></p><span className="rounded-lg bg-slate-100 px-2 py-1 text-[11px] font-bold text-slate-600 dark:bg-slate-800 dark:text-slate-300">{formatNumber(bucket.deal_count)}</span></div><p className="mt-3 text-lg font-black text-slate-950 dark:text-white">{money(bucket.weighted_value)}</p><p className="mt-1 text-xs text-slate-500"><T>Weighted</T> · {money(bucket.total_value)}</p></div>)}</div>
        </>}
      </V3Section>

      <V3Section title="Win / loss analytics" description="A deterministic conversion pulse for decided opportunities, separated from AI and external analytics services.">
        {!winLoss ? <V3Empty><T>No win/loss analytics are available yet.</T></V3Empty> : <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><MiniMetric label="Win rate" value={`${formatNumber(winLoss.win_rate)}%`} tone="emerald" /><MiniMetric label="Won deals" value={formatNumber(winLoss.won_count)} tone="emerald" /><MiniMetric label="Lost deals" value={formatNumber(winLoss.lost_count)} tone="rose" /><MiniMetric label="Open deals" value={formatNumber(winLoss.open_count)} tone="indigo" /></div>}
      </V3Section>

      <V3Section title="Report builder" description="Build safe grouped reports from live CRM data without exporting to a paid BI tool.">
        <div className="grid gap-3 md:grid-cols-4">
          <label className="text-xs font-bold text-slate-500"><T>Resource</T><select className="crm-select mt-2 w-full" onChange={(e) => { const next=e.target.value; setReportResource(next); setReportMetric(next === "deals" ? reportMetric : "count"); setReportGroupBy(next === "activities" ? "type" : "status"); }} value={reportResource}>{["deals","leads","tasks","activities"].map((item)=><option key={item} value={item}>{t(item)}</option>)}</select></label>
          <label className="text-xs font-bold text-slate-500"><T>Metric</T><select className="crm-select mt-2 w-full" onChange={(e)=>setReportMetric(e.target.value)} value={reportMetric}><option value="count">{t("Count")}</option>{reportResource === "deals" ? <><option value="sum_value">{t("Deal value")}</option><option value="weighted_value">{t("Weighted value")}</option></> : null}</select></label>
          <label className="text-xs font-bold text-slate-500"><T>Group by</T><select className="crm-select mt-2 w-full" onChange={(e)=>setReportGroupBy(e.target.value)} value={reportGroupBy}>{(reportResource === "deals" ? ["status","pipeline","stage","owner","currency"] : reportResource === "leads" ? ["status","source","owner"] : reportResource === "tasks" ? ["status","priority","owner"] : ["type","completed","owner"]).map((item)=><option key={item} value={item}>{t(item)}</option>)}</select></label>
          <div className="flex items-end"><Button className="w-full" disabled={reporting} onClick={()=>void runReport()}>{reporting?t("Building…"):t("Build report")}</Button></div>
        </div>
        {report ? <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">{report.rows.map((row)=>{const max=Math.max(...report.rows.map((item)=>Number(item.value)||0),1);const width=Math.max(4,Math.min(100,(Number(row.value)/max)*100));return <div className="rounded-2xl border border-slate-200/70 p-4 dark:border-slate-800" key={row.label}><div className="flex items-center justify-between gap-2"><p className="truncate text-sm font-black text-slate-900 dark:text-white"><T>{row.label}</T></p><span className="text-xs font-bold text-slate-400">{formatNumber(row.count)}</span></div><p className="mt-2 text-lg font-black text-slate-950 dark:text-white">{report.metric === "count" ? formatNumber(row.value) : forecast?.currency ? money(row.value) : formatNumber(row.value)}</p><div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800"><div className="h-full rounded-full bg-gradient-to-r from-violet-500 to-cyan-500" style={{width:`${width}%`}}/></div></div>})}</div> : <div className="mt-5"><V3Empty><T>Choose a metric and build a report.</T></V3Empty></div>}
      </V3Section>
    </section>
  );
}

function MiniMetric({ label, value, tone }: { label: string; value: string; tone: "rose" | "amber" | "violet" | "cyan" | "emerald" | "indigo" }) {
  const tones = { rose: "bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-300", amber: "bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-300", violet: "bg-violet-50 text-violet-700 dark:bg-violet-950/30 dark:text-violet-300", cyan: "bg-cyan-50 text-cyan-700 dark:bg-cyan-950/30 dark:text-cyan-300", emerald: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300", indigo: "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/30 dark:text-indigo-300" } as const;
  return <div className={`rounded-2xl px-4 py-3 ${tones[tone]}`}><p className="text-[10px] font-black uppercase tracking-[.12em]"><T>{label}</T></p><p className="mt-2 text-2xl font-black tabular-nums">{value}</p></div>;
}
