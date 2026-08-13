"use client";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { useCallback, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { ErrorState, LoadingState } from "@/components/ui/page-state";
import { PaginationControls } from "@/components/ui/pagination-controls";
import { TagForm } from "@/features/tags/tag-form";
import { TagList } from "@/features/tags/tag-list";
import { usePaginatedResource } from "@/hooks/use-paginated-resource";
import { ApiError } from "@/services/api-client";
import { tagService } from "@/services/tag-service";
import type { TagInput } from "@/types/tag";

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to save this tag.";
}

export function TagsWorkspace() {
  const { t } = useI18n();
  const [isCreating, setIsCreating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const [saveError, setSaveError] = useState<string | null>(null);
  const loadTags = useCallback(
    () => tagService.list({ page, page_size: 25, search: appliedSearch || undefined }),
    [appliedSearch, page],
  );
  const { error, isLoading, items, meta, reload } = usePaginatedResource(loadTags);

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setAppliedSearch(search.trim());
  }

  async function createTag(values: TagInput) {
    setIsSaving(true);
    setSaveError(null);
    try {
      await tagService.create(values);
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
          <h1 className="crm-title mt-3"><T>Tags</T></h1>
          <p className="crm-subtitle mt-3"><T>Create a shared vocabulary for segmenting CRM records.</T></p>
        </div>
        <Button aria-controls="new-tag-form" aria-expanded={isCreating} onClick={() => setIsCreating((open) => !open)}>
          {isCreating ? <T>Close form</T> : <T>Add tag</T>}
        </Button>
      </div>

      {isCreating ? (
        <div className="crm-card mt-8 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-6" id="new-tag-form">
          <h2 className="text-lg font-semibold text-slate-950 dark:text-white"><T>New tag</T></h2>
          <div className="mt-6"><TagForm isSubmitting={isSaving} onCancel={() => setIsCreating(false)} onSubmit={createTag} submitLabel="Create tag" /></div>
          {saveError ? <p className="mt-4 text-sm text-rose-700 dark:text-rose-200" role="alert"><T>{saveError}</T></p> : null}
        </div>
      ) : null}

      <form className="crm-toolbar mt-8 flex gap-3" onSubmit={submitSearch}>
        <label className="sr-only" htmlFor="tag-search"><T>Search tags</T></label>
        <input className="crm-input min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="tag-search" maxLength={100} onChange={(event) => setSearch(event.target.value)} placeholder={t("Search tags")} value={search} />
        <Button type="submit" variant="secondary"><T>Search</T></Button>
      </form>

      <div className="mt-6">
        {isLoading ? <LoadingState label="Loading tags..." /> : null}
        {!isLoading && error ? <ErrorState action={<Button onClick={reload}><T>Try again</T></Button>} description={error} title="Unable to load tags" /> : null}
        {!isLoading && !error ? <TagList tags={items} /> : null}
        {!error ? <PaginationControls isLoading={isLoading} meta={meta} onPageChange={setPage} /> : null}
      </div>
    </section>
  );
}
