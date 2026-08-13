"use client";

import { T, confirmDelete, useI18n } from "@/components/i18n/i18n-provider";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/page-state";
import { RecordMark } from "@/components/ui/record-mark";
import { SettingsNavigation } from "@/features/settings/settings-navigation";
import { RoleForm } from "@/features/settings/role-form";
import { ApiError } from "@/services/api-client";
import { roleService } from "@/services/role-service";
import type { UserPermission } from "@/types/auth";
import type { Role, RoleInput } from "@/types/role";

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to manage roles.";
}

export function RolesSettings() {
  const { formatNumber, locale, permissionLabel, t } = useI18n();
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<UserPermission[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [reloadNonce, setReloadNonce] = useState(0);

  useEffect(() => {
    let isActive = true;

    async function loadRolesAndPermissions() {
      setIsLoading(true);
      try {
        const [nextRoles, nextPermissions] = await Promise.all([
          roleService.list(),
          roleService.listPermissions(),
        ]);
        if (isActive) {
          setRoles(nextRoles);
          setPermissions(nextPermissions);
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

    void loadRolesAndPermissions();
    return () => {
      isActive = false;
    };
  }, [reloadNonce]);

  function reload() {
    setReloadNonce((value) => value + 1);
  }

  async function createRole(values: RoleInput) {
    setIsSaving(true);
    setSaveError(null);
    try {
      await roleService.create(values);
      setIsCreating(false);
      reload();
    } catch (caughtError) {
      setSaveError(getErrorMessage(caughtError));
    } finally {
      setIsSaving(false);
    }
  }

  async function updateRole(values: RoleInput) {
    if (!editingRole) {
      return;
    }

    setIsSaving(true);
    setSaveError(null);
    try {
      await roleService.update(editingRole.id, values);
      setEditingRole(null);
      reload();
    } catch (caughtError) {
      setSaveError(getErrorMessage(caughtError));
    } finally {
      setIsSaving(false);
    }
  }

  async function deleteRole(role: Role) {
    if (!confirmDelete(role.name)) {
      return;
    }

    setIsSaving(true);
    setSaveError(null);
    try {
      await roleService.remove(role.id);
      if (editingRole?.id === role.id) {
        setEditingRole(null);
      }
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
        <div><p className="crm-kicker"><T>Settings</T></p><h1 className="crm-title mt-3"><T>Roles & permissions</T></h1><p className="crm-subtitle mt-3"><T>Define access policies for people in your CRM workspace.</T></p></div>
        <Button aria-controls="create-role-form" aria-expanded={isCreating} disabled={permissions.length === 0} onClick={() => { setEditingRole(null); setIsCreating((value) => !value); }}>{isCreating ? <T>Close form</T> : <T>Add role</T>}</Button>
      </div>
      <div className="mt-6"><SettingsNavigation compact /></div>

      {isCreating ? <div className="crm-card mt-8 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-6" id="create-role-form"><h2 className="text-lg font-semibold text-slate-950 dark:text-white"><T>New role</T></h2><div className="mt-6"><RoleForm isSubmitting={isSaving} onCancel={() => setIsCreating(false)} onSubmit={createRole} permissions={permissions} submitLabel="Create role" /></div>{saveError ? <p className="mt-4 text-sm text-rose-700 dark:text-rose-200" role="alert">{t(saveError)}</p> : null}</div> : null}
      {editingRole ? <div className="crm-card mt-8 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-6"><h2 className="text-lg font-semibold text-slate-950 dark:text-white">{locale === "fa" ? `ویرایش ${editingRole.name}` : `Edit ${editingRole.name}`}</h2><div className="mt-6"><RoleForm initialRole={editingRole} isSubmitting={isSaving} key={editingRole.id} onCancel={() => setEditingRole(null)} onSubmit={updateRole} permissions={permissions} submitLabel="Save changes" /></div>{saveError ? <p className="mt-4 text-sm text-rose-700 dark:text-rose-200" role="alert">{t(saveError)}</p> : null}</div> : null}
      <div className="mt-8">{isLoading ? <LoadingState label="Loading roles..." /> : null}{!isLoading && error ? <ErrorState action={<Button onClick={reload}><T>Try again</T></Button>} description={error} title="Unable to load roles" /> : null}{!isLoading && !error && roles.length === 0 ? <EmptyState description="Create a role before adding more workspace members." title="No roles found" /> : null}{!isLoading && !error && roles.length > 0 ? <ul className="grid gap-4 lg:grid-cols-2">{roles.map((role) => <li className="crm-card crm-card-hover p-5" key={role.id}><div className="flex items-start justify-between gap-4"><div className="flex min-w-0 items-center gap-3"><RecordMark label={role.name} tone="indigo" /><div className="min-w-0"><h2 className="truncate text-lg font-bold tracking-[-.02em] text-slate-950 dark:text-white">{role.name}</h2><p className="mt-1 text-sm text-slate-500">{locale === "fa" ? `${formatNumber(role.permissions.length)} دسترسی` : `${formatNumber(role.permissions.length)} permission${role.permissions.length === 1 ? "" : "s"}`}</p></div></div><div className="flex gap-2"><Button onClick={() => { setIsCreating(false); setSaveError(null); setEditingRole(role); }} size="sm" variant="secondary"><T>Edit</T></Button><Button disabled={isSaving} onClick={() => void deleteRole(role)} size="sm" variant="danger"><T>Delete</T></Button></div></div><ul className="mt-4 flex flex-wrap gap-2">{role.permissions.map((permission) => <li className="rounded-lg border border-slate-200/70 bg-slate-50 px-2.5 py-1 text-[11px] font-semibold text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300" key={permission.id}>{permissionLabel(permission.name)}</li>)}</ul></li>)}</ul> : null}</div>
    </section>
  );
}
