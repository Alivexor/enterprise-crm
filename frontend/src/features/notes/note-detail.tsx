"use client";

import { LocalizedDateTime } from "@/components/i18n/localized-value";
import { T, confirmDelete } from "@/components/i18n/i18n-provider";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { AttachmentPanel } from "@/components/attachments/attachment-panel";
import { ErrorState, LoadingState } from "@/components/ui/page-state";
import { NoteForm } from "@/features/notes/note-form";
import { useCompanyOptions } from "@/hooks/use-company-options";
import { useContactOptions } from "@/hooks/use-contact-options";
import { useLeadOptions } from "@/hooks/use-lead-options";
import { ApiError } from "@/services/api-client";
import { noteService } from "@/services/note-service";
import type { Note, NoteInput } from "@/types/note";

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to load this note.";
}

function relatedPath(type: "company" | "contact" | "lead", id: string): string {
  const segmentByType = {
    company: "companies",
    contact: "contacts",
    lead: "leads",
  } as const;
  return `/dashboard/${segmentByType[type]}/${id}`;
}

export function NoteDetail({ noteId }: { noteId: string }) {
  const router = useRouter();
  const { companies } = useCompanyOptions();
  const { contacts } = useContactOptions();
  const { leads } = useLeadOptions();
  const [note, setNote] = useState<Note | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    let isActive = true;

    async function loadNote() {
      try {
        const nextNote = await noteService.get(noteId);
        if (isActive) {
          setNote(nextNote);
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

    void loadNote();
    return () => {
      isActive = false;
    };
  }, [noteId]);

  async function updateNote(values: NoteInput) {
    setIsSaving(true);
    try {
      const nextNote = await noteService.update(noteId, values);
      setNote(nextNote);
      setError(null);
      setIsEditing(false);
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    } finally {
      setIsSaving(false);
    }
  }

  async function deleteNote() {
    if (!confirmDelete()) {
      return;
    }

    setIsDeleting(true);
    try {
      await noteService.remove(noteId);
      router.replace("/dashboard/notes");
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
      setIsDeleting(false);
    }
  }

  if (isLoading) {
    return <LoadingState label="Loading note..." />;
  }

  if (!note) {
    return (
      <section className="crm-page mx-auto max-w-4xl">
        <Link className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/notes">
          <T>Back to notes</T>
        </Link>
        <div className="mt-6"><ErrorState description={error ?? "Note not found."} title="Unable to load note" /></div>
      </section>
    );
  }

  const initialValues: NoteInput = {
    company_id: note.company_id,
    contact_id: note.contact_id,
    content: note.content,
    lead_id: note.lead_id,
  };
  const relationships = [
    note.company_id ? { id: note.company_id, label: "Company", type: "company" as const } : null,
    note.contact_id ? { id: note.contact_id, label: "Contact", type: "contact" as const } : null,
    note.lead_id ? { id: note.lead_id, label: "Lead", type: "lead" as const } : null,
  ].filter((relationship): relationship is NonNullable<typeof relationship> => relationship !== null);

  return (
    <section className="crm-page mx-auto max-w-4xl">
      <Link className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/notes">
        <T>Back to notes</T>
      </Link>
      <div className="mt-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-7">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="crm-kicker"><T>Note</T></p>
            <h1 className="crm-title mt-3"><T>Customer context</T></h1>
            <p className="mt-2 text-sm text-slate-500"><T>Last updated</T> <LocalizedDateTime value={note.updated_at} /></p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setIsEditing((value) => !value)} variant="secondary">
              {isEditing ? <T>Close edit</T> : <T>Edit</T>}
            </Button>
            <Button disabled={isDeleting} onClick={() => void deleteNote()} variant="danger">
              {isDeleting ? <T>Deleting...</T> : <T>Delete</T>}
            </Button>
          </div>
        </div>

        {error ? <p className="mt-5 rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:bg-rose-950/50 dark:text-rose-200" role="alert"><T>{error}</T></p> : null}

        {isEditing ? (
          <div className="mt-6">
            <NoteForm companies={companies} contacts={contacts} initialValues={initialValues} isSubmitting={isSaving} key={note.id} leads={leads} onCancel={() => setIsEditing(false)} onSubmit={updateNote} submitLabel="Save changes" />
          </div>
        ) : (
          <div className="mt-6 border-t border-slate-100 pt-6 dark:border-slate-800">
            <p className="whitespace-pre-wrap text-sm leading-6 text-slate-800 dark:text-slate-100">{note.content}</p>
            <dl className="mt-7 grid gap-5 sm:grid-cols-2">
              <div>
                <dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Created</T></dt>
                <dd className="mt-2 text-sm text-slate-800 dark:text-slate-100"><LocalizedDateTime value={note.created_at} /></dd>
              </div>
              <div>
                <dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Related records</T></dt>
                <dd className="mt-2 flex flex-wrap gap-2">
                  {relationships.length === 0 ? <span className="text-sm text-slate-500"><T>General note</T></span> : relationships.map((relationship) => <Link className="rounded-md bg-indigo-50 px-2.5 py-1 text-xs font-semibold text-indigo-700 hover:bg-indigo-100 dark:bg-indigo-950/60 dark:text-indigo-200" href={relatedPath(relationship.type, relationship.id)} key={relationship.id}>{relationship.label}</Link>)}
                </dd>
              </div>
            </dl>
          </div>
        )}
        <AttachmentPanel entityId={note.id} entityType="note" />
      </div>
    </section>
  );
}
