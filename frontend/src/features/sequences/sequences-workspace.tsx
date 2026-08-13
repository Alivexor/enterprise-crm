"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast-provider";
import { V3Empty, V3Hero, V3Metric, V3Section } from "@/features/v3/v3-ui";
import { ApiError } from "@/services/api-client";
import { contactService } from "@/services/contact-service";
import { leadService } from "@/services/lead-service";
import { v3Service } from "@/services/v3-service";
import type { Contact } from "@/types/contact";
import type { Lead } from "@/types/lead";
import type { SalesSequence, SequenceEnrollment, SequenceStep } from "@/types/v3";

function errorMessage(error: unknown): string { return error instanceof ApiError ? error.message : "Unable to update sales sequences."; }

type DraftStep = { delay_days: number; action_type: "create_task" | "notify_owner"; title: string; priority: string; body: string };

const defaultStep = (): DraftStep => ({ delay_days: 0, action_type: "create_task", title: "Follow up", priority: "medium", body: "" });

export function SequencesWorkspace() {
  const { formatDateTime, formatNumber, t } = useI18n();
  const { notify } = useToast();
  const [sequences, setSequences] = useState<SalesSequence[]>([]);
  const [enrollments, setEnrollments] = useState<SequenceEnrollment[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [entityType, setEntityType] = useState<"lead" | "contact">("lead");
  const [steps, setSteps] = useState<DraftStep[]>([defaultStep(), { ...defaultStep(), delay_days: 2, action_type: "notify_owner", title: "Second touch" }]);
  const [selectedSequence, setSelectedSequence] = useState("");
  const [selectedEntity, setSelectedEntity] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [sequenceRows, enrollmentRows, leadRows, contactRows] = await Promise.all([
        v3Service.sequences.list(),
        v3Service.sequences.enrollments(),
        leadService.list({ page: 1, page_size: 100 }),
        contactService.list({ page: 1, page_size: 100 }),
      ]);
      setSequences(sequenceRows); setEnrollments(enrollmentRows); setLeads(leadRows.items); setContacts(contactRows.items);
      setSelectedSequence((current) => current || sequenceRows[0]?.id || "");
    } catch (cause) {
      notify({ tone: "error", title: t("Unable to load sequences"), description: t(errorMessage(cause)) });
    } finally { setLoading(false); }
  }, [notify, t]);
  useEffect(() => { void Promise.resolve().then(load); }, [load]);

  const selected = sequences.find((item) => item.id === selectedSequence) ?? null;
  const enrollmentRecords = selected?.entity_type === "contact" ? contacts.map((item) => ({ id: item.id, label: `${item.first_name} ${item.last_name}`.trim() || item.email || item.id })) : leads.map((item) => ({ id: item.id, label: item.title }));
  const activeEnrollments = enrollments.filter((item) => item.status === "active").length;
  const completedEnrollments = enrollments.filter((item) => item.status === "completed").length;

  function patchStep(index: number, patch: Partial<DraftStep>) { setSteps((current) => current.map((step, i) => i === index ? { ...step, ...patch } : step)); }
  function removeStep(index: number) { setSteps((current) => current.length <= 1 ? current : current.filter((_, i) => i !== index)); }

  async function createSequence(event: FormEvent) {
    event.preventDefault(); if (!name.trim() || !steps.length) return;
    setSaving(true);
    try {
      const payloadSteps: SequenceStep[] = steps.map((step) => ({
        delay_days: Math.max(0, Number(step.delay_days) || 0),
        action_type: step.action_type,
        config: step.action_type === "create_task"
          ? { title: step.title || "Follow up", priority: step.priority || "medium" }
          : { title: step.title || name.trim(), body: step.body || "Sequence follow-up is due." },
      }));
      const created = await v3Service.sequences.create({ name: name.trim(), description: description.trim() || null, entity_type: entityType, is_active: true, steps: payloadSteps });
      setName(""); setDescription(""); setSteps([defaultStep(), { ...defaultStep(), delay_days: 2, action_type: "notify_owner", title: "Second touch" }]);
      setSelectedSequence(created.id);
      notify({ tone: "success", title: t("Sequence created"), description: t("The cadence is ready for enrollment and is processed by the free local worker.") });
      await load();
    } catch (cause) { notify({ tone: "error", title: t("Unable to create sequence"), description: t(errorMessage(cause)) }); }
    finally { setSaving(false); }
  }

  async function enroll(event: FormEvent) {
    event.preventDefault(); if (!selectedSequence || !selectedEntity) return;
    setSaving(true);
    try { await v3Service.sequences.enroll(selectedSequence, { entity_id: selectedEntity }); setSelectedEntity(""); await load(); notify({ tone: "success", title: t("Record enrolled") }); }
    catch (cause) { notify({ tone: "error", title: t("Unable to enroll record"), description: t(errorMessage(cause)) }); }
    finally { setSaving(false); }
  }

  async function remove(sequence: SalesSequence) {
    if (!window.confirm(t("Delete this sequence?"))) return;
    try { await v3Service.sequences.remove(sequence.id); await load(); notify({ tone: "success", title: t("Sequence deleted") }); }
    catch (cause) { notify({ tone: "error", title: t("Unable to delete sequence"), description: t(errorMessage(cause)) }); }
  }

  const sortedEnrollments = useMemo(() => [...enrollments].sort((a, b) => b.started_at.localeCompare(a.started_at)).slice(0, 12), [enrollments]);

  return <section className="crm-page mx-auto max-w-[1500px] space-y-6">
    <V3Hero accent="amber" eyebrow="V3 Productivity" title="Sales sequences" description="Build no-cost follow-up cadences that create tasks and owner notifications on a schedule. The local worker processes due steps without a paid sales-engagement platform." />
    <div className="grid gap-4 sm:grid-cols-4"><V3Metric label="Sequences" value={formatNumber(sequences.length)} tone="amber"/><V3Metric label="Active enrollments" value={formatNumber(activeEnrollments)} tone="cyan"/><V3Metric label="Completed" value={formatNumber(completedEnrollments)} tone="emerald"/><V3Metric label="Automation cost" value={<T>Local / free</T>} tone="violet"/></div>

    <div className="grid gap-6 xl:grid-cols-[1.1fr_.9fr]">
      <V3Section title="Sequence builder" description="Each step can create a task or notify the record owner after a delay.">
        <form className="space-y-4" onSubmit={createSequence}>
          <div className="grid gap-3 sm:grid-cols-2"><input className="crm-input" onChange={(e)=>setName(e.target.value)} placeholder={t("Sequence name")} required value={name}/><select className="crm-select" onChange={(e)=>setEntityType(e.target.value as "lead"|"contact")} value={entityType}><option value="lead">{t("Lead")}</option><option value="contact">{t("Contact")}</option></select></div>
          <input className="crm-input w-full" onChange={(e)=>setDescription(e.target.value)} placeholder={t("Description")} value={description}/>
          <div className="space-y-3">{steps.map((step,index)=><article className="rounded-2xl border border-slate-200/75 bg-slate-50/65 p-4 dark:border-slate-800 dark:bg-slate-900/45" key={index}><div className="mb-3 flex items-center justify-between"><p className="text-xs font-black text-slate-500"><T>Step</T> {formatNumber(index+1)}</p><Button disabled={steps.length<=1} onClick={()=>removeStep(index)} size="sm" type="button" variant="tertiary">{t("Remove")}</Button></div><div className="grid gap-3 sm:grid-cols-[110px_1fr]"><label className="text-[11px] font-bold text-slate-500"><T>Delay days</T><input className="crm-input mt-1.5 w-full" min="0" onChange={(e)=>patchStep(index,{delay_days:Number(e.target.value)})} type="number" value={step.delay_days}/></label><label className="text-[11px] font-bold text-slate-500"><T>Action</T><select className="crm-select mt-1.5 w-full" onChange={(e)=>patchStep(index,{action_type:e.target.value as DraftStep["action_type"]})} value={step.action_type}><option value="create_task">{t("Create task")}</option><option value="notify_owner">{t("Notify owner")}</option></select></label></div><input className="crm-input mt-3 w-full" onChange={(e)=>patchStep(index,{title:e.target.value})} placeholder={t("Title")} value={step.title}/>{step.action_type==="create_task"?<select className="crm-select mt-3 w-full" onChange={(e)=>patchStep(index,{priority:e.target.value})} value={step.priority}><option value="low">{t("low")}</option><option value="medium">{t("medium")}</option><option value="high">{t("high")}</option><option value="urgent">{t("urgent")}</option></select>:<textarea className="crm-input mt-3 min-h-20 w-full" onChange={(e)=>patchStep(index,{body:e.target.value})} placeholder={t("Notification body")} value={step.body}/>}</article>)}</div>
          <div className="flex flex-wrap gap-2"><Button onClick={()=>setSteps((current)=>[...current,defaultStep()])} type="button" variant="secondary">{t("Add step")}</Button><Button disabled={saving||!name.trim()} type="submit">{t("Create sequence")}</Button></div>
        </form>
      </V3Section>

      <V3Section title="Enroll a record" description="Attach a lead or contact to an active sequence.">
        {sequences.length?<form className="space-y-3" onSubmit={enroll}><select className="crm-select w-full" onChange={(e)=>{setSelectedSequence(e.target.value);setSelectedEntity("");}} value={selectedSequence}>{sequences.map((item)=><option key={item.id} value={item.id}>{item.name} · {t(item.entity_type)}</option>)}</select><select className="crm-select w-full" onChange={(e)=>setSelectedEntity(e.target.value)} value={selectedEntity}><option value="">{t("Select a record")}</option>{enrollmentRecords.map((item)=><option key={item.id} value={item.id}>{item.label}</option>)}</select>{selected?<div className="rounded-2xl bg-slate-950 p-4 text-white"><p className="text-xs font-black">{selected.name}</p><p className="mt-2 text-[11px] leading-5 text-slate-400">{selected.steps.map((step,index)=>`${index+1}. +${step.delay_days}d ${t(step.action_type)}`).join("  →  ")}</p></div>:null}<Button className="w-full" disabled={saving||!selectedEntity} type="submit">{t("Enroll")}</Button></form>:<V3Empty><T>Create a sequence before enrolling records.</T></V3Empty>}
      </V3Section>
    </div>

    <V3Section title="Sequence library" description="Reusable follow-up cadences for your sales team.">{loading?<V3Empty><T>Loading sequences…</T></V3Empty>:sequences.length?<div className="grid gap-3 lg:grid-cols-2">{sequences.map((item)=><article className="rounded-2xl border border-slate-200/75 p-4 dark:border-slate-800" key={item.id}><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-black text-slate-950 dark:text-white">{item.name}</p><p className="mt-1 text-xs text-slate-500">{item.description||t("No description")}</p></div><Button onClick={()=>void remove(item)} size="sm" variant="danger">{t("Delete")}</Button></div><div className="mt-4 flex flex-wrap gap-2 text-[10px]"><span className="crm-chip"><T>{item.entity_type}</T></span><span className="crm-chip">{formatNumber(item.steps.length)} <T>steps</T></span><span className="crm-chip">{formatNumber(item.enrollment_count)} <T>enrollments</T></span></div></article>)}</div>:<V3Empty><T>No sequences yet.</T></V3Empty>}</V3Section>

    <V3Section title="Recent enrollments" description="Track cadence progress and failures.">{sortedEnrollments.length?<div className="overflow-x-auto"><table className="w-full min-w-[720px] text-sm"><thead className="text-[10px] uppercase tracking-[.1em] text-slate-400"><tr><th className="px-3 py-2 text-start"><T>Status</T></th><th className="px-3 py-2 text-start"><T>Record</T></th><th className="px-3 py-2 text-start"><T>Next step</T></th><th className="px-3 py-2 text-start"><T>Next run</T></th><th className="px-3 py-2 text-start"><T>Started</T></th></tr></thead><tbody>{sortedEnrollments.map((item)=><tr className="border-t border-slate-100 dark:border-slate-800" key={item.id}><td className="px-3 py-3 font-bold"><T>{item.status}</T></td><td className="px-3 py-3 font-mono text-xs text-slate-500" dir="ltr">{item.entity_id.slice(0,8)}…</td><td className="px-3 py-3">{formatNumber(item.next_step_position+1)}</td><td className="px-3 py-3 text-slate-500">{item.next_run_at?formatDateTime(item.next_run_at):"—"}</td><td className="px-3 py-3 text-slate-500">{formatDateTime(item.started_at)}</td></tr>)}</tbody></table></div>:<V3Empty><T>No sequence enrollments yet.</T></V3Empty>}</V3Section>
  </section>;
}
