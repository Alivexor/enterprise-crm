"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast-provider";
import { V3Empty, V3Hero, V3Metric, V3Section } from "@/features/v3/v3-ui";
import { ApiError } from "@/services/api-client";
import { v3Service } from "@/services/v3-service";
import type { Workflow, WorkflowAction, WorkflowCondition } from "@/types/v3";

const entityEvents: Record<string, string[]> = {
  lead: ["lead.created", "lead.updated", "manual"],
  deal: ["deal.created", "deal.updated", "manual"],
  task: ["task.created", "task.updated", "manual"],
  company: ["manual"],
};

const presets = [
  { name: "High-value deal follow-up", entity: "deal", event: "deal.updated", condition: { field: "value", operator: "gte", value: "100000" }, action: { type: "create_task", config: { title: "Review high-value opportunity", priority: "high", assigned_user: "owner" } } },
  { name: "Notify on converted lead", entity: "lead", event: "lead.updated", condition: { field: "status", operator: "eq", value: "converted" }, action: { type: "notify_user", config: { title: "Lead converted", message: "A lead has converted successfully.", user: "actor" } } },
  { name: "Urgent task guardrail", entity: "task", event: "task.updated", condition: { field: "priority", operator: "eq", value: "urgent" }, action: { type: "notify_user", config: { title: "Urgent task", message: "An urgent task needs attention.", user: "owner" } } },
] as const;

function errorMessage(error: unknown): string { return error instanceof ApiError ? error.message : "Unable to update workflow automation."; }

export function AutomationWorkspace() {
  const { formatDateTime, formatNumber, t } = useI18n();
  const { notify } = useToast();
  const [items, setItems] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [entity, setEntity] = useState("deal");
  const [eventType, setEventType] = useState("deal.updated");
  const [conditions, setConditions] = useState<WorkflowCondition[]>([{ field: "status", operator: "eq", value: "open" }]);
  const [actions, setActions] = useState<WorkflowAction[]>([{ type: "create_task", config: { title: "Follow up", priority: "medium", assigned_user: "owner" } }]);

  const load = useCallback(async () => {
    setLoading(true);
    try { setItems(await v3Service.automation.list()); }
    catch (cause) { notify({ tone: "error", title: t("Unable to load workflows"), description: t(errorMessage(cause)) }); }
    finally { setLoading(false); }
  }, [notify, t]);
  useEffect(() => { void Promise.resolve().then(load); }, [load]);

  const runs = useMemo(() => items.reduce((sum, item) => sum + item.run_count, 0), [items]);
  const active = items.filter((item) => item.is_active).length;

  function choosePreset(index: number) {
    const preset = presets[index];
    setName(preset.name); setDescription(""); setEntity(preset.entity); setEventType(preset.event);
    setConditions([{ ...preset.condition } as WorkflowCondition]);
    setActions([{ type: preset.action.type, config: { ...preset.action.config } } as WorkflowAction]);
  }

  function addCondition() { setConditions((current) => [...current, { field: "status", operator: "eq", value: "" }]); }
  function addAction() { setActions((current) => [...current, { type: "create_task", config: { title: "Follow up", priority: "medium", assigned_user: "owner" } }]); }

  async function create(event: FormEvent) {
    event.preventDefault();
    if (!name.trim() || !actions.length) return;
    setCreating(true);
    try {
      await v3Service.automation.create({ name: name.trim(), description: description.trim() || null, entity_type: entity, event_type: eventType, conditions, actions, is_active: true });
      notify({ tone: "success", title: t("Workflow created"), description: t("The automation is active and listening for matching CRM events.") });
      setName(""); setDescription("");
      await load();
    } catch (cause) { notify({ tone: "error", title: t("Unable to create workflow"), description: t(errorMessage(cause)) }); }
    finally { setCreating(false); }
  }

  async function toggle(item: Workflow) {
    try { await v3Service.automation.update(item.id, { is_active: !item.is_active }); await load(); }
    catch (cause) { notify({ tone: "error", title: t("Unable to update workflow"), description: t(errorMessage(cause)) }); }
  }

  async function remove(item: Workflow) {
    if (!window.confirm(t("Delete this workflow?"))) return;
    try { await v3Service.automation.remove(item.id); await load(); notify({ tone: "success", title: t("Workflow deleted") }); }
    catch (cause) { notify({ tone: "error", title: t("Unable to delete workflow"), description: t(errorMessage(cause)) }); }
  }

  return (
    <section className="crm-page mx-auto max-w-[1500px] space-y-6">
      <V3Hero accent="cyan" eyebrow="V3 Automation" title="Workflow studio" description="Build event-driven CRM automations with conditions and actions. Workflows execute inside the organization transaction boundary and require no paid automation platform." />
      <div className="grid gap-4 sm:grid-cols-3"><V3Metric label="Workflows" value={formatNumber(items.length)} tone="indigo" /><V3Metric label="Active workflows" value={formatNumber(active)} tone="emerald" /><V3Metric label="Total runs" value={formatNumber(runs)} tone="cyan" /></div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_.9fr]">
        <V3Section title="Automation library" description="Turn common sales rules into repeatable workflows.">
          {loading ? <V3Empty><T>Loading workflows…</T></V3Empty> : !items.length ? <V3Empty><T>No workflows yet. Build your first automation from the studio.</T></V3Empty> : <div className="space-y-3">{items.map((item) => <article className="rounded-2xl border border-slate-200/75 bg-slate-50/55 p-4 dark:border-slate-800 dark:bg-slate-900/45" key={item.id}><div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div><div className="flex flex-wrap items-center gap-2"><h3 className="text-sm font-black text-slate-950 dark:text-white">{item.name}</h3><span className={`rounded-lg px-2 py-1 text-[10px] font-black ${item.is_active ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300" : "bg-slate-100 text-slate-500 dark:bg-slate-800"}`}><T>{item.is_active ? "Active" : "Paused"}</T></span></div><p className="mt-1 text-xs text-slate-500">{item.description || t("No description")}</p><div className="mt-3 flex flex-wrap gap-2 text-[11px] text-slate-500"><span className="rounded-lg bg-white px-2 py-1 ring-1 ring-slate-200 dark:bg-slate-950 dark:ring-slate-800"><T>{item.entity_type}</T></span><span className="rounded-lg bg-white px-2 py-1 ring-1 ring-slate-200 dark:bg-slate-950 dark:ring-slate-800">{item.event_type}</span><span>{formatNumber(item.conditions.length)} <T>conditions</T></span><span>{formatNumber(item.actions.length)} <T>actions</T></span><span>{formatNumber(item.run_count)} <T>runs</T></span></div>{item.last_run_at ? <p className="mt-2 text-[11px] text-slate-400"><T>Last run</T>: {formatDateTime(item.last_run_at)}</p> : null}</div><div className="flex gap-2"><Button onClick={() => void toggle(item)} size="sm" variant="secondary">{item.is_active ? "Pause" : "Activate"}</Button><Button onClick={() => void remove(item)} size="sm" variant="danger">{t("Delete")}</Button></div></div></article>)}</div>}
        </V3Section>

        <V3Section title="Workflow templates" description="Start from a tested automation pattern and customize it.">
          <div className="space-y-2">{presets.map((preset, index) => <button className="w-full rounded-2xl border border-slate-200/75 bg-white p-4 text-start transition hover:-translate-y-0.5 hover:border-cyan-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-950 dark:hover:border-cyan-900" key={preset.name} onClick={() => choosePreset(index)} type="button"><p className="text-sm font-black text-slate-900 dark:text-white"><T>{preset.name}</T></p><p className="mt-1 text-xs text-slate-500">{preset.event} → <T>{preset.action.type}</T></p></button>)}</div>
        </V3Section>
      </div>

      <V3Section title="Visual workflow builder" description="Create a lightweight trigger → condition → action flow. Multiple conditions and actions are supported.">
        <form className="space-y-5" onSubmit={create}>
          <div className="grid gap-4 lg:grid-cols-2"><label className="text-sm font-bold text-slate-700 dark:text-slate-200"><T>Workflow name</T><input className="crm-input mt-2 w-full" maxLength={160} onChange={(e) => setName(e.target.value)} required value={name} /></label><label className="text-sm font-bold text-slate-700 dark:text-slate-200"><T>Description</T><input className="crm-input mt-2 w-full" maxLength={2000} onChange={(e) => setDescription(e.target.value)} value={description} /></label></div>
          <div className="grid gap-4 lg:grid-cols-2"><label className="text-sm font-bold text-slate-700 dark:text-slate-200"><T>Object</T><select className="crm-select mt-2 w-full" onChange={(e) => { const next = e.target.value; setEntity(next); setEventType(entityEvents[next][0]); }} value={entity}>{Object.keys(entityEvents).map((item) => <option key={item} value={item}>{t(item)}</option>)}</select></label><label className="text-sm font-bold text-slate-700 dark:text-slate-200"><T>Trigger</T><select className="crm-select mt-2 w-full" onChange={(e) => setEventType(e.target.value)} value={eventType}>{entityEvents[entity].map((item) => <option key={item} value={item}>{item}</option>)}</select></label></div>

          <div><div className="mb-3 flex items-center justify-between"><h3 className="text-sm font-black text-slate-900 dark:text-white"><T>Conditions</T></h3><Button onClick={addCondition} size="sm" variant="secondary">{t("Add condition")}</Button></div><div className="space-y-2">{conditions.map((condition, index) => <div className="grid gap-2 rounded-2xl border border-slate-200/70 bg-slate-50/55 p-3 md:grid-cols-[1fr_.8fr_1fr_auto] dark:border-slate-800 dark:bg-slate-900/40" key={`condition-${index}`}><input className="crm-input" onChange={(e) => setConditions((current) => current.map((item, i) => i === index ? { ...item, field: e.target.value } : item))} placeholder={t("Field, e.g. status")} value={condition.field} /><select className="crm-select" onChange={(e) => setConditions((current) => current.map((item, i) => i === index ? { ...item, operator: e.target.value as WorkflowCondition["operator"] } : item))} value={condition.operator}>{["eq","neq","contains","gt","gte","lt","lte","in","is_empty","not_empty"].map((operator) => <option key={operator} value={operator}>{operator}</option>)}</select><input className="crm-input" disabled={["is_empty","not_empty"].includes(condition.operator)} onChange={(e) => setConditions((current) => current.map((item, i) => i === index ? { ...item, value: e.target.value } : item))} placeholder={t("Value")} value={String(condition.value ?? "")} /><Button aria-label={t("Remove condition")} onClick={() => setConditions((current) => current.filter((_, i) => i !== index))} size="icon" variant="tertiary">×</Button></div>)}</div></div>

          <div><div className="mb-3 flex items-center justify-between"><h3 className="text-sm font-black text-slate-900 dark:text-white"><T>Actions</T></h3><Button onClick={addAction} size="sm" variant="secondary">{t("Add action")}</Button></div><div className="space-y-2">{actions.map((action, index) => <div className="rounded-2xl border border-slate-200/70 bg-slate-50/55 p-3 dark:border-slate-800 dark:bg-slate-900/40" key={`action-${index}`}><div className="flex gap-2"><select className="crm-select flex-1" onChange={(e) => setActions((current) => current.map((item, i) => i === index ? { type: e.target.value as WorkflowAction["type"], config: e.target.value === "create_task" ? { title: "Follow up", priority: "medium", assigned_user: "owner" } : e.target.value === "notify_user" ? { title: "CRM update", message: "A workflow matched.", user: "actor" } : { field: "status", value: "open" } } : item))} value={action.type}>{["create_task","notify_user","set_field"].map((type) => <option key={type} value={type}>{t(type)}</option>)}</select><Button aria-label={t("Remove action")} disabled={actions.length === 1} onClick={() => setActions((current) => current.filter((_, i) => i !== index))} size="icon" variant="tertiary">×</Button></div><textarea className="crm-input mt-2 min-h-20 w-full font-mono text-xs" onChange={(e) => { try { const config = JSON.parse(e.target.value); setActions((current) => current.map((item, i) => i === index ? { ...item, config } : item)); } catch { /* keep previous valid config */ } }} defaultValue={JSON.stringify(action.config, null, 2)} aria-label={t("Action configuration JSON")} /></div>)}</div></div>
          <div className="flex justify-end"><Button disabled={creating || !name.trim()} type="submit">{creating ? t("Creating…") : t("Create workflow")}</Button></div>
        </form>
      </V3Section>
    </section>
  );
}
