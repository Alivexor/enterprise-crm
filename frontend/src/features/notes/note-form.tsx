"use client";

import { T } from "@/components/i18n/i18n-provider";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import type { Company } from "@/types/company";
import type { Contact } from "@/types/contact";
import type { Lead } from "@/types/lead";
import type { NoteInput } from "@/types/note";

type NoteFormProps = {
  companies: Company[];
  contacts: Contact[];
  initialValues?: NoteInput;
  isSubmitting: boolean;
  leads: Lead[];
  onCancel?: () => void;
  onSubmit: (values: NoteInput) => Promise<void>;
  submitLabel: string;
};

const emptyNote: NoteInput = {
  company_id: null,
  contact_id: null,
  content: "",
  lead_id: null,
};

const fieldClassName =
  "w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950";

export function NoteForm({
  companies,
  contacts,
  initialValues = emptyNote,
  isSubmitting,
  leads,
  onCancel,
  onSubmit,
  submitLabel,
}: NoteFormProps) {
  const [content, setContent] = useState(initialValues.content);
  const [companyId, setCompanyId] = useState(initialValues.company_id ?? "");
  const [contactId, setContactId] = useState(initialValues.contact_id ?? "");
  const [leadId, setLeadId] = useState(initialValues.lead_id ?? "");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      company_id: companyId || null,
      contact_id: contactId || null,
      content: content.trim(),
      lead_id: leadId || null,
    });
  }

  return (
    <form className="space-y-5" onSubmit={(event) => void handleSubmit(event)}>
      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="note-content">
          <T>Note</T>
        </label>
        <textarea
          className={`${fieldClassName} min-h-36 resize-y`}
          id="note-content"
          maxLength={20_000}
          minLength={1}
          onChange={(event) => setContent(event.target.value)}
          required
          value={content}
        />
      </div>

      <div className="grid gap-5 sm:grid-cols-3">
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="note-company">
            <T>Company</T> <span className="font-normal text-slate-500"><T>(optional)</T></span>
          </label>
          <select className={fieldClassName} id="note-company" onChange={(event) => setCompanyId(event.target.value)} value={companyId}>
            <option value=""><T>No company</T></option>
            {companies.map((company) => <option key={company.id} value={company.id}>{company.name}</option>)}
          </select>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="note-contact">
            <T>Contact</T> <span className="font-normal text-slate-500"><T>(optional)</T></span>
          </label>
          <select className={fieldClassName} id="note-contact" onChange={(event) => setContactId(event.target.value)} value={contactId}>
            <option value=""><T>No contact</T></option>
            {contacts.map((contact) => <option key={contact.id} value={contact.id}>{contact.first_name} {contact.last_name}</option>)}
          </select>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="note-lead">
            <T>Lead</T> <span className="font-normal text-slate-500"><T>(optional)</T></span>
          </label>
          <select className={fieldClassName} id="note-lead" onChange={(event) => setLeadId(event.target.value)} value={leadId}>
            <option value=""><T>No lead</T></option>
            {leads.map((lead) => <option key={lead.id} value={lead.id}>{lead.title}</option>)}
          </select>
        </div>
      </div>

      <div className="flex flex-col-reverse gap-3 pt-1 sm:flex-row sm:justify-end">
        {onCancel ? <Button disabled={isSubmitting} onClick={onCancel} variant="tertiary"><T>Cancel</T></Button> : null}
        <Button disabled={isSubmitting} type="submit">
          {isSubmitting ? <T>Saving...</T> : <T>{submitLabel}</T>}
        </Button>
      </div>
    </form>
  );
}
