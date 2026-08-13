"use client";

import { T, confirmDelete } from "@/components/i18n/i18n-provider";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { AttachmentPanel } from "@/components/attachments/attachment-panel";
import { ErrorState, LoadingState } from "@/components/ui/page-state";
import { CompanyForm } from "@/features/companies/company-form";
import { CustomFieldsPanel } from "@/features/custom-fields/custom-fields-panel";
import { RelationshipHealthCard } from "@/features/intelligence/relationship-health-card";
import { CompanyRelationshipOverview } from "@/features/companies/company-relationship-overview";
import { ApiError } from "@/services/api-client";
import { companyService } from "@/services/company-service";
import type { Company, CompanyInput } from "@/types/company";

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to load this company.";
}

export function CompanyDetail({ companyId }: { companyId: string }) {
  const router = useRouter();
  const [company, setCompany] = useState<Company | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    let isActive = true;

    async function loadCompany() {
      try {
        const nextCompany = await companyService.get(companyId);
        if (isActive) {
          setCompany(nextCompany);
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

    void loadCompany();
    return () => {
      isActive = false;
    };
  }, [companyId]);

  async function updateCompany(values: CompanyInput) {
    setIsSaving(true);
    try {
      const updatedCompany = await companyService.update(companyId, values);
      setCompany(updatedCompany);
      setError(null);
      setIsEditing(false);
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    } finally {
      setIsSaving(false);
    }
  }

  async function deleteCompany() {
    if (!confirmDelete(company?.name)) {
      return;
    }

    setIsDeleting(true);
    try {
      await companyService.remove(companyId);
      router.replace("/dashboard/companies");
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
      setIsDeleting(false);
    }
  }

  if (isLoading) {
    return <LoadingState label="Loading company…" />;
  }

  if (company === null) {
    return (
      <section className="crm-page mx-auto max-w-4xl">
        <Link
          className="text-sm font-medium text-indigo-600 hover:text-indigo-500 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-200 dark:text-indigo-300 dark:focus-visible:ring-indigo-950"
          href="/dashboard/companies"
        >
          <T>← Back to companies</T>
        </Link>
        <div className="mt-6">
          <ErrorState
            description={error ?? "Company not found."}
            title="Unable to load company"
          />
        </div>
      </section>
    );
  }

  const companyInput: CompanyInput = {
    industry: company.industry,
    name: company.name,
    website: company.website,
  };

  return (
    <section className="crm-page mx-auto max-w-4xl">
      <Link
        className="text-sm font-medium text-indigo-600 hover:text-indigo-500 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-200 dark:text-indigo-300 dark:focus-visible:ring-indigo-950"
        href="/dashboard/companies"
      >
        <T>← Back to companies</T>
      </Link>
      <div className="crm-card mt-6 flex flex-col gap-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-7">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex min-w-0 items-start gap-4">
            <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 via-violet-500 to-cyan-500 text-xl font-black text-white shadow-[0_12px_28px_rgba(79,70,229,.22)] ring-1 ring-inset ring-white/20">{company.name.charAt(0).toUpperCase()}</span>
            <div className="min-w-0">
              <p className="crm-kicker"><T>Company</T></p>
              <h1 className="crm-title mt-3 truncate">{company.name}</h1>
              <div className="mt-3 flex flex-wrap gap-2">{company.industry ? <span className="crm-chip">{company.industry}</span> : null}{company.website ? <span className="crm-chip" data-bidi="ltr">{company.website.replace(/^https?:\/\//, "")}</span> : null}</div>
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setIsEditing((editing) => !editing)} variant="secondary">
              {isEditing ? <T>Close edit</T> : <T>Edit</T>}
            </Button>
            <Button
              disabled={isDeleting}
              onClick={() => void deleteCompany()}
              variant="danger"
            >
              {isDeleting ? <T>Deleting…</T> : <T>Delete</T>}
            </Button>
          </div>
        </div>

        {error ? (
          <p
            className="rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:bg-rose-950/50 dark:text-rose-200"
            role="alert"
          >
            <T>{error}</T>
          </p>
        ) : null}

        {isEditing ? (
          <CompanyForm
            initialValues={companyInput}
            isSubmitting={isSaving}
            key={company.id}
            onCancel={() => setIsEditing(false)}
            onSubmit={updateCompany}
            submitLabel="Save changes"
          />
        ) : (
          <dl className="grid gap-4 border-t border-slate-100 pt-6 sm:grid-cols-2 dark:border-slate-800">
            <div className="rounded-2xl bg-slate-50/70 p-4 ring-1 ring-inset ring-slate-200/60 dark:bg-slate-900/45 dark:ring-slate-800">
              <dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Industry</T></dt>
              <dd className="mt-2 text-sm text-slate-800 dark:text-slate-100">{company.industry ?? "—"}</dd>
            </div>
            <div className="rounded-2xl bg-slate-50/70 p-4 ring-1 ring-inset ring-slate-200/60 dark:bg-slate-900/45 dark:ring-slate-800">
              <dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Website</T></dt>
              <dd className="mt-2 text-sm text-slate-800 dark:text-slate-100">
                {company.website ? (
                  <a
                    className="text-indigo-600 hover:text-indigo-500 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-200 dark:text-indigo-300 dark:focus-visible:ring-indigo-950"
                    href={company.website}
                    rel="noreferrer"
                    target="_blank"
                  >
                    {company.website}
                  </a>
                ) : (
                  "—"
                )}
              </dd>
            </div>
          </dl>
        )}
        <RelationshipHealthCard companyId={company.id} />
        <CompanyRelationshipOverview companyId={company.id} />
        <CustomFieldsPanel entityId={company.id} entityType="company" />
        <AttachmentPanel entityId={company.id} entityType="company" />
      </div>
    </section>
  );
}
