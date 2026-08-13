"use client";

import { T } from "@/components/i18n/i18n-provider";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import type { PipelineInput } from "@/types/pipeline";

type PipelineFormProps = { initialValues?: PipelineInput; isSubmitting: boolean; onCancel?: () => void; onSubmit: (input: PipelineInput) => Promise<void>; submitLabel: string };
const emptyPipeline: PipelineInput = { description: null, name: "" };

export function PipelineForm({ initialValues = emptyPipeline, isSubmitting, onCancel, onSubmit, submitLabel }: PipelineFormProps) {
  const [name, setName] = useState(initialValues.name); const [description, setDescription] = useState(initialValues.description ?? "");
  async function handleSubmit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); await onSubmit({ description: description.trim() || null, name: name.trim() }); }
  return <form className="space-y-5" onSubmit={(event) => void handleSubmit(event)}><div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="pipeline-name"><T>Pipeline name</T></label><input className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="pipeline-name" maxLength={255} minLength={1} onChange={(event) => setName(event.target.value)} required value={name} /></div><div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="pipeline-description"><T>Description</T> <span className="font-normal text-slate-500"><T>(optional)</T></span></label><textarea className="crm-textarea min-h-28 w-full resize-y rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="pipeline-description" maxLength={20000} onChange={(event) => setDescription(event.target.value)} value={description} /></div><div className="flex flex-col-reverse gap-3 pt-1 sm:flex-row sm:justify-end">{onCancel ? <Button disabled={isSubmitting} onClick={onCancel} variant="tertiary"><T>Cancel</T></Button> : null}<Button disabled={isSubmitting} type="submit">{isSubmitting ? <T>Saving…</T> : <T>{submitLabel}</T>}</Button></div></form>;
}
