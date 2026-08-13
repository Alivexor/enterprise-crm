"use client";

import { LocalizedEnum } from "@/components/i18n/localized-value";
import { T } from "@/components/i18n/i18n-provider";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { activityTypes, type ActivityInput } from "@/types/activity";
import { toDateTimeLocalValue, toIsoDateTime } from "@/utils/date";

type ActivityFormProps = {
  initialValues?: ActivityInput;
  isSubmitting: boolean;
  onCancel?: () => void;
  onSubmit: (values: ActivityInput) => Promise<void>;
  submitLabel: string;
};

const emptyActivity: ActivityInput = { company_id: null, completed: false, contact_id: null, description: null, due_date: null, lead_id: null, title: "", type: "call" };

export function ActivityForm({ initialValues = emptyActivity, isSubmitting, onCancel, onSubmit, submitLabel }: ActivityFormProps) {
  const [type, setType] = useState(initialValues.type);
  const [title, setTitle] = useState(initialValues.title);
  const [description, setDescription] = useState(initialValues.description ?? "");
  const [dueDate, setDueDate] = useState(toDateTimeLocalValue(initialValues.due_date));
  const [completed, setCompleted] = useState(initialValues.completed);
  async function handleSubmit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); await onSubmit({ company_id: null, completed, contact_id: null, description: description.trim() || null, due_date: toIsoDateTime(dueDate), lead_id: null, title: title.trim(), type }); }
  return <form className="space-y-5" onSubmit={(event) => void handleSubmit(event)}><div className="grid gap-5 sm:grid-cols-[minmax(0,1fr)_minmax(0,1.5fr)]"><div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="activity-type"><T>Type</T></label><select className="crm-select w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="activity-type" onChange={(event) => setType(event.target.value as ActivityInput["type"])} value={type}>{activityTypes.map((value) => <option key={value} value={value}><LocalizedEnum value={value} /></option>)}</select></div><div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="activity-title"><T>Title</T></label><input className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="activity-title" maxLength={255} minLength={1} onChange={(event) => setTitle(event.target.value)} required value={title} /></div></div><div className="grid gap-5 sm:grid-cols-2"><div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="activity-due-date"><T>Due date</T> <span className="font-normal text-slate-500"><T>(optional)</T></span></label><input className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="activity-due-date" onChange={(event) => setDueDate(event.target.value)} type="datetime-local" value={dueDate} /></div><label className="flex items-end gap-3 pb-2 text-sm font-medium text-slate-800 dark:text-slate-100"><input checked={completed} className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500" onChange={(event) => setCompleted(event.target.checked)} type="checkbox" /><T>Mark as completed</T></label></div><div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="activity-description"><T>Description</T> <span className="font-normal text-slate-500"><T>(optional)</T></span></label><textarea className="crm-textarea min-h-28 w-full resize-y rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="activity-description" maxLength={20000} onChange={(event) => setDescription(event.target.value)} value={description} /></div><div className="flex flex-col-reverse gap-3 pt-1 sm:flex-row sm:justify-end">{onCancel ? <Button disabled={isSubmitting} onClick={onCancel} variant="tertiary"><T>Cancel</T></Button> : null}<Button disabled={isSubmitting} type="submit">{isSubmitting ? <T>Saving…</T> : <T>{submitLabel}</T>}</Button></div></form>;
}
