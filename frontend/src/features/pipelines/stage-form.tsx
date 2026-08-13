"use client";

import { T } from "@/components/i18n/i18n-provider";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import type { PipelineStageInput } from "@/types/pipeline";

type StageFormProps = { initialValues?: PipelineStageInput; isSubmitting: boolean; onCancel?: () => void; onSubmit: (input: PipelineStageInput) => Promise<void>; submitLabel: string };
const emptyStage: PipelineStageInput = { name: "", order: 0, probability: 0 };

export function StageForm({ initialValues = emptyStage, isSubmitting, onCancel, onSubmit, submitLabel }: StageFormProps) {
  const [name, setName] = useState(initialValues.name); const [order, setOrder] = useState(String(initialValues.order)); const [probability, setProbability] = useState(String(initialValues.probability));
  async function handleSubmit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); await onSubmit({ name: name.trim(), order: Number(order), probability: Number(probability) }); }
  return <form className="grid gap-4 rounded-lg border border-slate-200 p-4 dark:border-slate-800 sm:grid-cols-[minmax(0,1fr)_8rem_8rem_auto]" onSubmit={(event) => void handleSubmit(event)}><div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="stage-name"><T>Stage name</T></label><input className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="stage-name" maxLength={100} minLength={1} onChange={(event) => setName(event.target.value)} required value={name} /></div><div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="stage-order"><T>Order</T></label><input className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="stage-order" min="0" onChange={(event) => setOrder(event.target.value)} required type="number" value={order} /></div><div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="stage-probability"><T>Probability</T></label><input className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="stage-probability" max="100" min="0" onChange={(event) => setProbability(event.target.value)} required step="0.01" type="number" value={probability} /></div><div className="flex items-end gap-2">{onCancel ? <Button disabled={isSubmitting} onClick={onCancel} size="sm" variant="tertiary"><T>Cancel</T></Button> : null}<Button disabled={isSubmitting} size="sm" type="submit">{isSubmitting ? <T>Saving…</T> : <T>{submitLabel}</T>}</Button></div></form>;
}
