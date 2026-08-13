"use client";

import { T } from "@/components/i18n/i18n-provider";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import type { Company } from "@/types/company";
import type { ContactInput } from "@/types/contact";

type ContactFormProps = {
  companies: Company[];
  initialValues?: ContactInput;
  isSubmitting: boolean;
  onCancel?: () => void;
  onSubmit: (values: ContactInput) => Promise<void>;
  submitLabel: string;
};

const emptyContact: ContactInput = {
  company_id: "",
  email: null,
  first_name: "",
  last_name: "",
  phone: null,
};

export function ContactForm({
  companies,
  initialValues = emptyContact,
  isSubmitting,
  onCancel,
  onSubmit,
  submitLabel,
}: ContactFormProps) {
  const [companyId, setCompanyId] = useState(initialValues.company_id);
  const [firstName, setFirstName] = useState(initialValues.first_name);
  const [lastName, setLastName] = useState(initialValues.last_name);
  const [email, setEmail] = useState(initialValues.email ?? "");
  const [phone, setPhone] = useState(initialValues.phone ?? "");
  const hasCompanies = companies.length > 0;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      company_id: companyId,
      email: email.trim() || null,
      first_name: firstName.trim(),
      last_name: lastName.trim(),
      phone: phone.trim() || null,
    });
  }

  return (
    <form className="space-y-5" onSubmit={(event) => void handleSubmit(event)}>
      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="contact-company">
          <T>Company</T>
        </label>
        <select
          className="crm-select w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950"
          disabled={!hasCompanies || isSubmitting}
          id="contact-company"
          onChange={(event) => setCompanyId(event.target.value)}
          required
          value={companyId}
        >
          <option value=""><T>Select a company</T></option>
          {companies.map((company) => (
            <option key={company.id} value={company.id}>
              {company.name}
            </option>
          ))}
        </select>
        {!hasCompanies ? (
          <p className="text-sm text-slate-500"><T>Create a company before adding a contact.</T></p>
        ) : null}
      </div>
      <div className="grid gap-5 sm:grid-cols-2">
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="contact-first-name">
            <T>First name</T>
          </label>
          <input
            autoComplete="given-name"
            className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950"
            id="contact-first-name"
            maxLength={100}
            minLength={1}
            onChange={(event) => setFirstName(event.target.value)}
            required
            value={firstName}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="contact-last-name">
            <T>Last name</T>
          </label>
          <input
            autoComplete="family-name"
            className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950"
            id="contact-last-name"
            maxLength={100}
            minLength={1}
            onChange={(event) => setLastName(event.target.value)}
            required
            value={lastName}
          />
        </div>
      </div>
      <div className="grid gap-5 sm:grid-cols-2">
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="contact-email">
            <T>Email</T> <span className="font-normal text-slate-500"><T>(optional)</T></span>
          </label>
          <input
            autoComplete="email"
            className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950"
            id="contact-email"
            maxLength={320}
            onChange={(event) => setEmail(event.target.value)}
            type="email"
            value={email}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="contact-phone">
            <T>Phone</T> <span className="font-normal text-slate-500"><T>(optional)</T></span>
          </label>
          <input
            autoComplete="tel"
            className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950"
            id="contact-phone"
            maxLength={50}
            onChange={(event) => setPhone(event.target.value)}
            type="tel"
            value={phone}
          />
        </div>
      </div>
      <div className="flex flex-col-reverse gap-3 pt-1 sm:flex-row sm:justify-end">
        {onCancel ? (
          <Button disabled={isSubmitting} onClick={onCancel} variant="tertiary">
            <T>Cancel</T>
          </Button>
        ) : null}
        <Button disabled={isSubmitting || !hasCompanies} type="submit">
          {isSubmitting ? <T>Saving…</T> : <T>{submitLabel}</T>}
        </Button>
      </div>
    </form>
  );
}
