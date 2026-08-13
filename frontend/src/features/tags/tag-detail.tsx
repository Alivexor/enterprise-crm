"use client";

import { LocalizedDateTime, LocalizedEnum } from "@/components/i18n/localized-value";
import { T, useI18n, confirmDelete } from "@/components/i18n/i18n-provider";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { ErrorState, LoadingState } from "@/components/ui/page-state";
import { TagForm } from "@/features/tags/tag-form";
import { ApiError } from "@/services/api-client";
import { tagService } from "@/services/tag-service";
import { tagEntityTypes, type Tag, type TagEntityType, type TagInput } from "@/types/tag";

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to load this tag.";
}

type AssignmentAction = "assign" | "unassign";

export function TagDetail({ tagId }: { tagId: string }) {
  const { t } = useI18n();
  const router = useRouter();
  const [tag, setTag] = useState<Tag | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [assignmentAction, setAssignmentAction] = useState<AssignmentAction>("assign");
  const [entityType, setEntityType] = useState<TagEntityType>("company");
  const [entityId, setEntityId] = useState("");
  const [assignmentMessage, setAssignmentMessage] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    async function loadTag() {
      try {
        const nextTag = await tagService.get(tagId);
        if (isActive) {
          setTag(nextTag);
          setError(null);
        }
      } catch (caughtError) {
        if (isActive) {
          setError(getErrorMessage(caughtError));
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void loadTag();
    return () => {
      isActive = false;
    };
  }, [tagId]);

  async function updateTag(values: TagInput) {
    setIsSaving(true);
    try {
      const nextTag = await tagService.update(tagId, values);
      setTag(nextTag);
      setError(null);
      setIsEditing(false);
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    } finally {
      setIsSaving(false);
    }
  }

  async function deleteTag() {
    if (!confirmDelete(tag?.name)) {
      return;
    }

    setIsDeleting(true);
    try {
      await tagService.remove(tagId);
      router.replace("/dashboard/tags");
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
      setIsDeleting(false);
    }
  }

  async function updateAssignment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setAssignmentMessage(null);
    try {
      if (assignmentAction === "assign") {
        await tagService.assign(tagId, entityType, entityId.trim());
      } else {
        await tagService.unassign(tagId, entityType, entityId.trim());
      }
      setAssignmentMessage(
        assignmentAction === "assign" ? "Tag assigned successfully." : "Tag removed successfully.",
      );
      setEntityId("");
    } catch (caughtError) {
      setAssignmentMessage(getErrorMessage(caughtError));
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) {
    return <LoadingState label="Loading tag..." />;
  }

  if (!tag) {
    return (
      <section className="crm-page mx-auto max-w-4xl">
        <Link className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/tags"><T>Back to tags</T></Link>
        <div className="mt-6"><ErrorState description={error ?? "Tag not found."} title="Unable to load tag" /></div>
      </section>
    );
  }

  return (
    <section className="crm-page mx-auto max-w-4xl">
      <Link className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/tags"><T>Back to tags</T></Link>
      <div className="crm-card mt-6 p-5 sm:p-7">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="crm-kicker"><T>Tag</T></p>
            <div className="mt-2 flex items-center gap-3">
              <span aria-hidden="true" className="h-5 w-5 rounded-full ring-2 ring-white dark:ring-slate-950" style={{ backgroundColor: tag.color }} />
              <h1 className="text-3xl font-semibold tracking-tight text-slate-950 dark:text-white">{tag.name}</h1>
            </div>
            <p className="mt-2 text-sm text-slate-500"><T>Created</T> <LocalizedDateTime value={tag.created_at} /></p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setIsEditing((value) => !value)} variant="secondary">{isEditing ? <T>Close edit</T> : <T>Edit</T>}</Button>
            <Button disabled={isDeleting} onClick={() => void deleteTag()} variant="danger">{isDeleting ? <T>Deleting...</T> : <T>Delete</T>}</Button>
          </div>
        </div>

        {error ? <p className="mt-5 rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:bg-rose-950/50 dark:text-rose-200" role="alert"><T>{error}</T></p> : null}

        {isEditing ? <div className="mt-6 border-t border-slate-100 pt-6 dark:border-slate-800"><TagForm initialValues={{ color: tag.color, name: tag.name }} isSubmitting={isSaving} key={tag.id} onCancel={() => setIsEditing(false)} onSubmit={updateTag} submitLabel="Save changes" /></div> : null}

        <div className="mt-8 border-t border-slate-100 pt-6 dark:border-slate-800">
          <h2 className="text-lg font-semibold text-slate-950 dark:text-white"><T>Apply this tag</T></h2>
          <p className="mt-1 text-sm leading-6 text-slate-500"><T>Assign or remove this tag from an existing company, contact, lead, or deal using its record ID.</T></p>
          <form className="mt-5 grid gap-4 sm:grid-cols-[10rem_1fr_auto]" onSubmit={(event) => void updateAssignment(event)}>
            <div>
              <label className="sr-only" htmlFor="assignment-action"><T>Action</T></label>
              <select className="crm-select w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-950 outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="assignment-action" onChange={(event) => setAssignmentAction(event.target.value as AssignmentAction)} value={assignmentAction}>
                <option value="assign"><T>Assign</T></option>
                <option value="unassign"><T>Remove</T></option>
              </select>
            </div>
            <div className="grid grid-cols-[9rem_1fr] gap-3">
              <label className="sr-only" htmlFor="tag-entity-type"><T>Record type</T></label>
              <select className="crm-select rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-950 outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="tag-entity-type" onChange={(event) => setEntityType(event.target.value as TagEntityType)} value={entityType}>
                {tagEntityTypes.map((type) => <option key={type} value={type}><LocalizedEnum value={type} /></option>)}
              </select>
              <div>
                <label className="sr-only" htmlFor="tag-entity-id"><T>Record ID</T></label>
                <input className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-950 outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="tag-entity-id" onChange={(event) => setEntityId(event.target.value)} placeholder={t("Record UUID")} required value={entityId} />
              </div>
            </div>
            <Button disabled={isSaving} type="submit" variant="secondary">{isSaving ? <T>Saving...</T> : assignmentAction === "assign" ? <T>Assign tag</T> : <T>Remove tag</T>}</Button>
          </form>
          {assignmentMessage ? <p className="mt-4 text-sm text-slate-600 dark:text-slate-300" role="status">{assignmentMessage}</p> : null}
        </div>
      </div>
    </section>
  );
}
