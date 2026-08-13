"use client";

import { LocalizedEnum } from "@/components/i18n/localized-value";
import { T } from "@/components/i18n/i18n-provider";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { taskPriorities, taskStatuses, type TaskInput } from "@/types/task";
import { toDateTimeLocalValue, toIsoDateTime } from "@/utils/date";

type TaskFormProps = {
  initialValues?: TaskInput;
  isSubmitting: boolean;
  onCancel?: () => void;
  onSubmit: (values: TaskInput) => Promise<void>;
  submitLabel: string;
};

const emptyTask: TaskInput = { description: null, due_date: null, priority: "medium", status: "open", title: "" };

export function TaskForm({ initialValues = emptyTask, isSubmitting, onCancel, onSubmit, submitLabel }: TaskFormProps) {
  const [title, setTitle] = useState(initialValues.title);
  const [description, setDescription] = useState(initialValues.description ?? "");
  const [priority, setPriority] = useState(initialValues.priority);
  const [status, setStatus] = useState(initialValues.status);
  const [dueDate, setDueDate] = useState(toDateTimeLocalValue(initialValues.due_date));

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({ description: description.trim() || null, due_date: toIsoDateTime(dueDate), priority, status, title: title.trim() });
  }

  return (
    <form className="space-y-5" onSubmit={(event) => void handleSubmit(event)}>
      <div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="task-title"><T>Task title</T></label><input className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="task-title" maxLength={255} minLength={1} onChange={(event) => setTitle(event.target.value)} required value={title} /></div>
      <div className="grid gap-5 sm:grid-cols-3"><div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="task-priority"><T>Priority</T></label><select className="crm-select w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="task-priority" onChange={(event) => setPriority(event.target.value as TaskInput["priority"])} value={priority}>{taskPriorities.map((value) => <option key={value} value={value}><LocalizedEnum value={value} /></option>)}</select></div><div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="task-status"><T>Status</T></label><select className="crm-select w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="task-status" onChange={(event) => setStatus(event.target.value as TaskInput["status"])} value={status}>{taskStatuses.map((value) => <option key={value} value={value}><LocalizedEnum value={value} /></option>)}</select></div><div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="task-due-date"><T>Due date</T> <span className="font-normal text-slate-500"><T>(optional)</T></span></label><input className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="task-due-date" onChange={(event) => setDueDate(event.target.value)} type="datetime-local" value={dueDate} /></div></div>
      <div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="task-description"><T>Description</T> <span className="font-normal text-slate-500"><T>(optional)</T></span></label><textarea className="crm-textarea min-h-28 w-full resize-y rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="task-description" maxLength={20000} onChange={(event) => setDescription(event.target.value)} value={description} /></div>
      <div className="flex flex-col-reverse gap-3 pt-1 sm:flex-row sm:justify-end">{onCancel ? <Button disabled={isSubmitting} onClick={onCancel} variant="tertiary"><T>Cancel</T></Button> : null}<Button disabled={isSubmitting} type="submit">{isSubmitting ? <T>Saving…</T> : <T>{submitLabel}</T>}</Button></div>
    </form>
  );
}
