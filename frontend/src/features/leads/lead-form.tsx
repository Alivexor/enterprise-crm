"use client";

import { LocalizedEnum } from "@/components/i18n/localized-value";
import { T } from "@/components/i18n/i18n-provider";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import type { Company } from "@/types/company";
import { leadSources, leadStatuses, type LeadInput } from "@/types/lead";

type LeadFormProps = {
  companies: Company[];
  initialValues?: LeadInput;
  isSubmitting: boolean;
  onCancel?: () => void;
  onSubmit: (values: LeadInput) => Promise<void>;
  submitLabel: string;
};

const emptyLead: LeadInput = {
  company_id: null,
  contact_id: null,
  description: null,
  source: "other",
  status: "new",
  title: "",
};

export function LeadForm({
  companies,
  initialValues = emptyLead,
  isSubmitting,
  onCancel,
  onSubmit,
  submitLabel,
}: LeadFormProps) {
  const [title, setTitle] = useState(initialValues.title);
  const [description, setDescription] = useState(initialValues.description ?? "");
  const [source, setSource] = useState(initialValues.source);
  const [status, setStatus] = useState(initialValues.status);
  const [companyId, setCompanyId] = useState(initialValues.company_id ?? "");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      company_id: companyId || null,
      contact_id: null,
      description: description.trim() || null,
      source,
      status,
      title: title.trim(),
    });
  }

  return (
    <form className="space-y-5" onSubmit={(event) => void handleSubmit(event)}>
      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="lead-title"><T>Lead title</T></label>
        <input
          className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950"
          id="lead-title"
          maxLength={255}
          minLength={1}
          onChange={(event) => setTitle(event.target.value)}
          required
          value={title}
        />
      </div>
      <div className="grid gap-5 sm:grid-cols-2">
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="lead-source"><T>Source</T></label>
          <select className="crm-select w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="lead-source" onChange={(event) => setSource(event.target.value as LeadInput["source"])} value={source}>
            {leadSources.map((value) => <option key={value} value={value}><LocalizedEnum value={value} /></option>)}
          </select>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="lead-status"><T>Status</T></label>
          <select className="crm-select w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="lead-status" onChange={(event) => setStatus(event.target.value as LeadInput["status"])} value={status}>
            {leadStatuses.map((value) => <option key={value} value={value}><LocalizedEnum value={value} /></option>)}
          </select>
        </div>
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="lead-company"><T>Company</T> <span className="font-normal text-slate-500"><T>(optional)</T></span></label>
        <select className="crm-select w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="lead-company" onChange={(event) => setCompanyId(event.target.value)} value={companyId}>
          <option value=""><T>No company yet</T></option>
          {companies.map((company) => <option key={company.id} value={company.id}>{company.name}</option>)}
        </select>
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="lead-description"><T>Description</T> <span className="font-normal text-slate-500"><T>(optional)</T></span></label>
        <textarea className="crm-textarea min-h-28 w-full resize-y rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="lead-description" maxLength={20000} onChange={(event) => setDescription(event.target.value)} value={description} />
      </div>
      <div className="flex flex-col-reverse gap-3 pt-1 sm:flex-row sm:justify-end">
        {onCancel ? <Button disabled={isSubmitting} onClick={onCancel} variant="tertiary"><T>Cancel</T></Button> : null}
        <Button disabled={isSubmitting} type="submit">{isSubmitting ? <T>Saving…</T> : <T>{submitLabel}</T>}</Button>
      </div>
    </form>
  );
}
