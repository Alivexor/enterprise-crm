"use client";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { useCallback, useMemo, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { ErrorState, LoadingState } from "@/components/ui/page-state";
import { PaginationControls } from "@/components/ui/pagination-controls";
import { ContactForm } from "@/features/contacts/contact-form";
import { ContactList } from "@/features/contacts/contact-list";
import { useCompanyOptions } from "@/hooks/use-company-options";
import { usePaginatedResource } from "@/hooks/use-paginated-resource";
import { ApiError } from "@/services/api-client";
import { contactService } from "@/services/contact-service";
import type { ContactInput } from "@/types/contact";

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to save this contact.";
}

export function ContactsWorkspace({ initialCreate = false }: { initialCreate?: boolean } = {}) {
  const { t } = useI18n();
  const [isCreating, setIsCreating] = useState(initialCreate);
  const [isSaving, setIsSaving] = useState(false);
  const [page, setPage] = useState(1);
  const [companyId, setCompanyId] = useState("");
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const [saveError, setSaveError] = useState<string | null>(null);
  const { companies, error: companiesError } = useCompanyOptions();
  const loadContacts = useCallback(
    () =>
      contactService.list({
        company_id: companyId || undefined,
        page,
        page_size: 25,
        search: appliedSearch || undefined,
        sort_by: "last_name",
        sort_direction: "asc",
      }),
    [appliedSearch, companyId, page],
  );
  const { error, isLoading, items, meta, reload } = usePaginatedResource(loadContacts);
  const companyNames = useMemo(
    () => new Map(companies.map((company) => [company.id, company.name])),
    [companies],
  );

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setAppliedSearch(search.trim());
  }

  async function createContact(values: ContactInput) {
    setIsSaving(true);
    setSaveError(null);
    try {
      await contactService.create(values);
      setIsCreating(false);
      reload();
    } catch (caughtError) {
      setSaveError(getErrorMessage(caughtError));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="crm-page mx-auto max-w-6xl">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="crm-kicker"><T>CRM</T></p>
          <h1 className="crm-title mt-3"><T>Contacts</T></h1>
          <p className="crm-subtitle mt-3"><T>Manage the people at your customer companies.</T></p>
        </div>
        <Button aria-controls="new-contact-form" aria-expanded={isCreating} onClick={() => setIsCreating((open) => !open)}>
          {isCreating ? <T>Close form</T> : <T>Add contact</T>}
        </Button>
      </div>

      {companiesError ? (
        <div className="mt-6" role="alert">
          <ErrorState description={companiesError} title="Unable to load company options" />
        </div>
      ) : null}

      {isCreating ? (
        <div className="crm-card mt-8 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-6" id="new-contact-form">
          <h2 className="text-lg font-semibold text-slate-950 dark:text-white"><T>New contact</T></h2>
          <p className="mt-1 text-sm text-slate-500"><T>Add a person to an existing company.</T></p>
          <div className="mt-6">
            <ContactForm
              companies={companies}
              isSubmitting={isSaving}
              onCancel={() => setIsCreating(false)}
              onSubmit={createContact}
              submitLabel="Create contact"
            />
          </div>
          {saveError ? <p className="mt-4 text-sm text-rose-700 dark:text-rose-200" role="alert"><T>{saveError}</T></p> : null}
        </div>
      ) : null}

      <form className="crm-toolbar mt-8 flex flex-col gap-3 sm:flex-row" onSubmit={submitSearch}>
        <label className="sr-only" htmlFor="contact-search"><T>Search contacts</T></label>
        <input
          className="crm-input min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950"
          id="contact-search"
          onChange={(event) => setSearch(event.target.value)}
          placeholder={t("Search contacts")}
          value={search}
        />
        <label className="sr-only" htmlFor="contact-company-filter"><T>Filter by company</T></label>
        <select
          className="crm-select rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950"
          id="contact-company-filter"
          onChange={(event) => {
            setCompanyId(event.target.value);
            setPage(1);
          }}
          value={companyId}
        >
          <option value=""><T>All companies</T></option>
          {companies.map((company) => <option key={company.id} value={company.id}>{company.name}</option>)}
        </select>
        <Button type="submit" variant="secondary"><T>Search</T></Button>
      </form>

      <div className="mt-6">
        {isLoading ? <LoadingState label="Loading contacts…" /> : null}
        {!isLoading && error ? (
          <ErrorState action={<Button onClick={reload}><T>Try again</T></Button>} description={error} title="Unable to load contacts" />
        ) : null}
        {!isLoading && !error ? <ContactList companyNames={companyNames} contacts={items} /> : null}
        {!error ? <PaginationControls isLoading={isLoading} meta={meta} onPageChange={setPage} /> : null}
      </div>
    </section>
  );
}
