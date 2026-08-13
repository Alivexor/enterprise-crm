"use client";

import { LocalizedDateTime } from "@/components/i18n/localized-value";
import { T } from "@/components/i18n/i18n-provider";
import { useEffect, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { ErrorState, LoadingState } from "@/components/ui/page-state";
import { SettingsNavigation } from "@/features/settings/settings-navigation";
import { ApiError } from "@/services/api-client";
import { organizationService } from "@/services/organization-service";
import type { Organization } from "@/types/organization";

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to load organization settings.";
}

export function OrganizationSettings() {
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [reloadNonce, setReloadNonce] = useState(0);

  useEffect(() => {
    let isActive = true;

    async function loadOrganization() {
      try {
        const nextOrganization = await organizationService.get();
        if (isActive) {
          setOrganization(nextOrganization);
          setName(nextOrganization.name);
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

    void loadOrganization();
    return () => {
      isActive = false;
    };
  }, [reloadNonce]);

  async function updateOrganization(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setMessage(null);
    try {
      const nextOrganization = await organizationService.update({ name: name.trim() });
      setOrganization(nextOrganization);
      setName(nextOrganization.name);
      setError(null);
      setMessage("Organization updated successfully.");
    } catch (caughtError) {
      setMessage(getErrorMessage(caughtError));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="crm-page mx-auto max-w-4xl">
      <p className="crm-kicker"><T>Settings</T></p>
      <h1 className="crm-title mt-3"><T>Organization</T></h1>
      <p className="crm-subtitle mt-3"><T>Manage the workspace identity shared by your CRM team.</T></p>
      <div className="mt-6"><SettingsNavigation compact /></div>
      <div className="mt-8">
        {isLoading ? <LoadingState label="Loading organization..." /> : null}
        {!isLoading && error ? <ErrorState action={<Button onClick={() => setReloadNonce((value) => value + 1)}><T>Try again</T></Button>} description={error} title="Unable to load organization" /> : null}
        {!isLoading && organization ? <form className="crm-card rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-6" onSubmit={(event) => void updateOrganization(event)}><h2 className="text-lg font-semibold text-slate-950 dark:text-white"><T>Workspace details</T></h2><div className="mt-6 space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="organization-name"><T>Organization name</T></label><input className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="organization-name" maxLength={255} minLength={1} onChange={(event) => setName(event.target.value)} required value={name} /></div><dl className="mt-6 grid gap-4 border-t border-slate-100 pt-6 text-sm dark:border-slate-800 sm:grid-cols-2"><div><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Organization ID</T></dt><dd className="mt-2 break-all text-slate-700 dark:text-slate-200">{organization.id}</dd></div><div><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Created</T></dt><dd className="mt-2 text-slate-700 dark:text-slate-200"><LocalizedDateTime value={organization.created_at} /></dd></div></dl><div className="mt-6 flex items-center justify-between gap-4"><p className="text-sm text-slate-500" role="status">{message}</p><Button disabled={isSaving} type="submit">{isSaving ? <T>Saving...</T> : <T>Save organization</T>}</Button></div></form> : null}
      </div>
    </section>
  );
}
