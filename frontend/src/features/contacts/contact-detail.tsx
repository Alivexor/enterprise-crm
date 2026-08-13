"use client";

import { T, confirmDelete } from "@/components/i18n/i18n-provider";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { AttachmentPanel } from "@/components/attachments/attachment-panel";
import { ErrorState, LoadingState } from "@/components/ui/page-state";
import { ContactForm } from "@/features/contacts/contact-form";
import { CustomFieldsPanel } from "@/features/custom-fields/custom-fields-panel";
import { useCompanyOptions } from "@/hooks/use-company-options";
import { ApiError } from "@/services/api-client";
import { contactService } from "@/services/contact-service";
import type { Contact, ContactInput } from "@/types/contact";

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to load this contact.";
}

export function ContactDetail({ contactId }: { contactId: string }) {
  const router = useRouter();
  const [contact, setContact] = useState<Contact | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const { companies, isLoading: isLoadingCompanies } = useCompanyOptions();
  const companyNames = useMemo(() => new Map(companies.map((company) => [company.id, company.name])), [companies]);

  useEffect(() => {
    let isActive = true;
    async function loadContact() {
      try {
        const nextContact = await contactService.get(contactId);
        if (isActive) {
          setContact(nextContact);
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
    void loadContact();
    return () => { isActive = false; };
  }, [contactId]);

  async function updateContact(values: ContactInput) {
    setIsSaving(true);
    try {
      const nextContact = await contactService.update(contactId, values);
      setContact(nextContact);
      setError(null);
      setIsEditing(false);
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    } finally {
      setIsSaving(false);
    }
  }

  async function deleteContact() {
    if (!confirmDelete(contact ? `${contact.first_name} ${contact.last_name}`.trim() : undefined)) {
      return;
    }
    setIsDeleting(true);
    try {
      await contactService.remove(contactId);
      router.replace("/dashboard/contacts");
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
      setIsDeleting(false);
    }
  }

  if (isLoading) {
    return <LoadingState label="Loading contact…" />;
  }
  if (!contact) {
    return (
      <section className="crm-page mx-auto max-w-4xl">
        <Link className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/contacts"><T>← Back to contacts</T></Link>
        <div className="mt-6"><ErrorState description={error ?? "Contact not found."} title="Unable to load contact" /></div>
      </section>
    );
  }

  return (
    <section className="crm-page mx-auto max-w-4xl">
      <Link className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/contacts"><T>← Back to contacts</T></Link>
      <div className="crm-card mt-6 flex flex-col gap-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-7">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="crm-kicker"><T>Contact</T></p>
            <h1 className="crm-title mt-3">{contact.first_name} {contact.last_name}</h1>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setIsEditing((value) => !value)} variant="secondary">{isEditing ? <T>Close edit</T> : <T>Edit</T>}</Button>
            <Button disabled={isDeleting} onClick={() => void deleteContact()} variant="danger">{isDeleting ? <T>Deleting…</T> : <T>Delete</T>}</Button>
          </div>
        </div>
        {error ? <p className="rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:bg-rose-950/50 dark:text-rose-200" role="alert"><T>{error}</T></p> : null}
        {isEditing ? (
          isLoadingCompanies ? <LoadingState label="Loading company options…" /> : <ContactForm companies={companies} initialValues={contact} isSubmitting={isSaving} key={contact.id} onCancel={() => setIsEditing(false)} onSubmit={updateContact} submitLabel="Save changes" />
        ) : (
          <dl className="grid gap-6 border-t border-slate-100 pt-6 sm:grid-cols-2 dark:border-slate-800">
            <div><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Company</T></dt><dd className="mt-2 text-sm text-slate-800 dark:text-slate-100">{companyNames.get(contact.company_id) ?? <T>Unknown company</T>}</dd></div>
            <div><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Email</T></dt><dd className="mt-2 text-sm text-slate-800 dark:text-slate-100">{contact.email ?? "—"}</dd></div>
            <div><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Phone</T></dt><dd className="mt-2 text-sm text-slate-800 dark:text-slate-100">{contact.phone ?? "—"}</dd></div>
          </dl>
        )}
        <CustomFieldsPanel entityId={contact.id} entityType="contact" />
        <AttachmentPanel entityId={contact.id} entityType="contact" />
      </div>
    </section>
  );
}
