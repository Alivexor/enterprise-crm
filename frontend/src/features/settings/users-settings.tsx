"use client";

import { LocalizedDateTime } from "@/components/i18n/localized-value";
import { T, useI18n } from "@/components/i18n/i18n-provider";
import { useCallback, useEffect, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/page-state";
import { PaginationControls } from "@/components/ui/pagination-controls";
import { RecordMark } from "@/components/ui/record-mark";
import { StatusBadge } from "@/components/ui/status-badge";
import { SettingsNavigation } from "@/features/settings/settings-navigation";
import { UserForm } from "@/features/settings/user-form";
import { usePaginatedResource } from "@/hooks/use-paginated-resource";
import { ApiError } from "@/services/api-client";
import { roleService } from "@/services/role-service";
import { userManagementService } from "@/services/user-management-service";
import type { Role } from "@/types/role";
import type { ManagedUser, ManagedUserCreate, ManagedUserUpdate } from "@/types/user-management";

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to manage users.";
}

export function UsersSettings() {
  const { locale, t } = useI18n();
  const [roles, setRoles] = useState<Role[]>([]);
  const [rolesError, setRolesError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [editingUser, setEditingUser] = useState<ManagedUser | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const [saveError, setSaveError] = useState<string | null>(null);
  const loadUsers = useCallback(
    () => userManagementService.list({ page, page_size: 25, search: appliedSearch || undefined }),
    [appliedSearch, page],
  );
  const { error, isLoading, items, meta, reload } = usePaginatedResource(loadUsers);

  useEffect(() => {
    let isActive = true;

    async function loadRoles() {
      try {
        const nextRoles = await roleService.list();
        if (isActive) {
          setRoles(nextRoles);
          setRolesError(null);
        }
      } catch (caughtError) {
        if (isActive) {
          setRolesError(getErrorMessage(caughtError));
        }
      }
    }

    void loadRoles();
    return () => {
      isActive = false;
    };
  }, []);

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setAppliedSearch(search.trim());
  }

  async function createUser(values: ManagedUserCreate | ManagedUserUpdate) {
    setIsSaving(true);
    setSaveError(null);
    try {
      await userManagementService.create(values as ManagedUserCreate);
      setIsCreating(false);
      reload();
    } catch (caughtError) {
      setSaveError(getErrorMessage(caughtError));
    } finally {
      setIsSaving(false);
    }
  }

  async function updateUser(values: ManagedUserCreate | ManagedUserUpdate) {
    if (!editingUser) {
      return;
    }
    setIsSaving(true);
    setSaveError(null);
    try {
      await userManagementService.update(editingUser.id, values as ManagedUserUpdate);
      setEditingUser(null);
      reload();
    } catch (caughtError) {
      setSaveError(getErrorMessage(caughtError));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="crm-page mx-auto max-w-6xl">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="crm-kicker"><T>Settings</T></p><h1 className="crm-title mt-3"><T>Users</T></h1><p className="crm-subtitle mt-3"><T>Manage people who can access this CRM workspace.</T></p></div><Button aria-controls="create-user-form" aria-expanded={isCreating} disabled={roles.length === 0} onClick={() => { setEditingUser(null); setIsCreating((value) => !value); }}>{isCreating ? <T>Close form</T> : <T>Add user</T>}</Button></div>
      <div className="mt-6"><SettingsNavigation compact /></div>
      {rolesError ? <div className="mt-6"><ErrorState description={rolesError} title="Unable to load roles" /></div> : null}
      {isCreating ? <div className="crm-card mt-8 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-6" id="create-user-form"><h2 className="text-lg font-semibold text-slate-950 dark:text-white"><T>New user</T></h2><div className="mt-6"><UserForm isSubmitting={isSaving} mode="create" onCancel={() => setIsCreating(false)} onSubmit={createUser} roles={roles} /></div>{saveError ? <p className="mt-4 text-sm text-rose-700 dark:text-rose-200" role="alert"><T>{saveError}</T></p> : null}</div> : null}
      {editingUser ? <div className="crm-card mt-8 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-6"><h2 className="text-lg font-semibold text-slate-950 dark:text-white">{locale === "fa" ? `ویرایش ${editingUser.first_name} ${editingUser.last_name}` : `Edit ${editingUser.first_name} ${editingUser.last_name}`}</h2><div className="mt-6"><UserForm initialUser={editingUser} isSubmitting={isSaving} key={editingUser.id} mode="edit" onCancel={() => setEditingUser(null)} onSubmit={updateUser} roles={roles} /></div>{saveError ? <p className="mt-4 text-sm text-rose-700 dark:text-rose-200" role="alert"><T>{saveError}</T></p> : null}</div> : null}
      <form className="crm-toolbar mt-8 flex gap-3" onSubmit={submitSearch}><label className="sr-only" htmlFor="users-search"><T>Search users</T></label><input className="crm-input min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="users-search" onChange={(event) => setSearch(event.target.value)} placeholder={t("Search users")} value={search} /><Button type="submit" variant="secondary"><T>Search</T></Button></form>
      <div className="mt-6">{isLoading ? <LoadingState label="Loading users..." /> : null}{!isLoading && error ? <ErrorState action={<Button onClick={reload}><T>Try again</T></Button>} description={error} title="Unable to load users" /> : null}{!isLoading && !error && items.length === 0 ? <EmptyState description="Add a team member once you are ready to share the workspace." title="No users found" /> : null}{!isLoading && !error && items.length > 0 ? <div className="crm-table-shell overflow-x-auto"><table className="w-full min-w-180 text-start text-sm"><thead className="border-b border-slate-100 text-xs tracking-wide text-slate-500 uppercase dark:border-slate-800"><tr><th className="px-5 py-3 font-semibold"><T>User</T></th><th className="px-5 py-3 font-semibold"><T>Roles</T></th><th className="px-5 py-3 font-semibold"><T>Status</T></th><th className="px-5 py-3 font-semibold"><T>Joined</T></th><th className="px-5 py-3"><span className="sr-only"><T>Actions</T></span></th></tr></thead><tbody className="divide-y divide-slate-100 dark:divide-slate-800">{items.map((managedUser) => <tr key={managedUser.id}><td className="px-5 py-4"><div className="flex items-center gap-3"><RecordMark label={`${managedUser.first_name} ${managedUser.last_name}`} tone="slate" /><div className="min-w-0"><p className="truncate font-bold text-slate-900 dark:text-white">{managedUser.first_name} {managedUser.last_name}</p><p className="mt-1 truncate text-xs text-slate-500" data-bidi="ltr">{managedUser.email}</p></div></div></td><td className="px-5 py-4 text-slate-600 dark:text-slate-300">{managedUser.roles.map((role) => role.name).join(", ") || t("No roles")}</td><td className="px-5 py-4"><StatusBadge tone={managedUser.is_active ? "green" : "gray"}>{t(managedUser.is_active ? "Active" : "Inactive")}</StatusBadge></td><td className="px-5 py-4 text-slate-500"><LocalizedDateTime value={managedUser.created_at} /></td><td className="px-5 py-4 text-end"><Button onClick={() => { setIsCreating(false); setSaveError(null); setEditingUser(managedUser); }} size="sm" variant="secondary"><T>Edit</T></Button></td></tr>)}</tbody></table></div> : null}{!error ? <PaginationControls isLoading={isLoading} meta={meta} onPageChange={setPage} /> : null}</div>
    </section>
  );
}
