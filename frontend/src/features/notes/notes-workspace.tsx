"use client";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { useCallback, useMemo, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { ErrorState, LoadingState } from "@/components/ui/page-state";
import { PaginationControls } from "@/components/ui/pagination-controls";
import { NoteForm } from "@/features/notes/note-form";
import { NoteList } from "@/features/notes/note-list";
import { useCompanyOptions } from "@/hooks/use-company-options";
import { useContactOptions } from "@/hooks/use-contact-options";
import { useLeadOptions } from "@/hooks/use-lead-options";
import { usePaginatedResource } from "@/hooks/use-paginated-resource";
import { ApiError } from "@/services/api-client";
import { noteService } from "@/services/note-service";
import type { NoteInput } from "@/types/note";

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to save this note.";
}

export function NotesWorkspace({ initialCreate = false }: { initialCreate?: boolean } = {}) {
  const { t } = useI18n();
  const { companies, error: companiesError } = useCompanyOptions();
  const { contacts, error: contactsError } = useContactOptions();
  const { leads, error: leadsError } = useLeadOptions();
  const [isCreating, setIsCreating] = useState(initialCreate);
  const [isSaving, setIsSaving] = useState(false);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const [saveError, setSaveError] = useState<string | null>(null);

  const loadNotes = useCallback(
    () => noteService.list({ page, page_size: 25, search: appliedSearch || undefined }),
    [appliedSearch, page],
  );
  const { error, isLoading, items, meta, reload } = usePaginatedResource(loadNotes);
  const companyNames = useMemo(
    () => new Map(companies.map((company) => [company.id, company.name])),
    [companies],
  );
  const associationError = companiesError ?? contactsError ?? leadsError;

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setAppliedSearch(search.trim());
  }

  async function createNote(values: NoteInput) {
    setIsSaving(true);
    setSaveError(null);
    try {
      await noteService.create(values);
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
          <h1 className="crm-title mt-3"><T>Notes</T></h1>
          <p className="crm-subtitle mt-3"><T>Keep durable context about customer relationships in one place.</T></p>
        </div>
        <Button aria-controls="new-note-form" aria-expanded={isCreating} onClick={() => setIsCreating((open) => !open)}>
          {isCreating ? <T>Close form</T> : <T>Add note</T>}
        </Button>
      </div>

      {isCreating ? (
        <div className="crm-card mt-8 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-6" id="new-note-form">
          <h2 className="text-lg font-semibold text-slate-950 dark:text-white"><T>New note</T></h2>
          {associationError ? <p className="mt-3 text-sm text-amber-700 dark:text-amber-200" role="status"><T>Some related records could not be loaded. You can still save a general note.</T></p> : null}
          <div className="mt-6">
            <NoteForm companies={companies} contacts={contacts} isSubmitting={isSaving} leads={leads} onCancel={() => setIsCreating(false)} onSubmit={createNote} submitLabel="Create note" />
          </div>
          {saveError ? <p className="mt-4 text-sm text-rose-700 dark:text-rose-200" role="alert"><T>{saveError}</T></p> : null}
        </div>
      ) : null}

      <form className="crm-toolbar mt-8 flex gap-3" onSubmit={submitSearch}>
        <label className="sr-only" htmlFor="note-search"><T>Search notes</T></label>
        <input className="crm-input min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="note-search" onChange={(event) => setSearch(event.target.value)} placeholder={t("Search notes")} value={search} />
        <Button type="submit" variant="secondary"><T>Search</T></Button>
      </form>

      <div className="mt-6">
        {isLoading ? <LoadingState label="Loading notes..." /> : null}
        {!isLoading && error ? <ErrorState action={<Button onClick={reload}><T>Try again</T></Button>} description={error} title="Unable to load notes" /> : null}
        {!isLoading && !error ? <NoteList companyNames={companyNames} notes={items} /> : null}
        {!error ? <PaginationControls isLoading={isLoading} meta={meta} onPageChange={setPage} /> : null}
      </div>
    </section>
  );
}
