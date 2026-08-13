"use client";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import type { CompanyInput } from "@/types/company";

type CompanyFormProps = {
  initialValues?: CompanyInput;
  isSubmitting: boolean;
  onCancel?: () => void;
  onSubmit: (values: CompanyInput) => Promise<void>;
  submitLabel: string;
};

const emptyCompany: CompanyInput = {
  industry: null,
  name: "",
  website: null,
};

export function CompanyForm({
  initialValues = emptyCompany,
  isSubmitting,
  onCancel,
  onSubmit,
  submitLabel,
}: CompanyFormProps) {
  const { t } = useI18n();
  const [name, setName] = useState(initialValues.name);
  const [website, setWebsite] = useState(initialValues.website ?? "");
  const [industry, setIndustry] = useState(initialValues.industry ?? "");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({
      industry: industry.trim() || null,
      name: name.trim(),
      website: website.trim() || null,
    });
  }

  return (
    <form className="space-y-5" onSubmit={(event) => void handleSubmit(event)}>
      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="company-name">
          <T>Company name</T>
        </label>
        <input
          autoComplete="organization"
          className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950"
          id="company-name"
          maxLength={255}
          minLength={1}
          onChange={(event) => setName(event.target.value)}
          required
          value={name}
        />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="company-website">
          <T>Website</T> <span className="font-normal text-slate-500"><T>(optional)</T></span>
        </label>
        <input
          className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950"
          id="company-website"
          maxLength={2048}
          onChange={(event) => setWebsite(event.target.value)}
          placeholder="https://example.com"
          type="url"
          value={website}
        />
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="company-industry">
          <T>Industry</T> <span className="font-normal text-slate-500"><T>(optional)</T></span>
        </label>
        <input
          className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950"
          id="company-industry"
          maxLength={255}
          onChange={(event) => setIndustry(event.target.value)}
          placeholder={t("e.g. Software")}
          value={industry}
        />
      </div>
      <div className="flex flex-col-reverse gap-3 pt-1 sm:flex-row sm:justify-end">
        {onCancel ? (
          <Button disabled={isSubmitting} onClick={onCancel} variant="tertiary">
            <T>Cancel</T>
          </Button>
        ) : null}
        <Button disabled={isSubmitting} type="submit">
          {isSubmitting ? <T>Saving…</T> : <T>{submitLabel}</T>}
        </Button>
      </div>
    </form>
  );
}
