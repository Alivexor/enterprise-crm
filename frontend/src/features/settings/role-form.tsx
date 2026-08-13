"use client";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import type { UserPermission } from "@/types/auth";
import type { Role, RoleInput } from "@/types/role";

type RoleFormProps = {
  initialRole?: Role;
  isSubmitting: boolean;
  onCancel?: () => void;
  onSubmit: (values: RoleInput) => Promise<void>;
  permissions: UserPermission[];
  submitLabel: string;
};

export function RoleForm({
  initialRole,
  isSubmitting,
  onCancel,
  onSubmit,
  permissions,
  submitLabel,
}: RoleFormProps) {
  const { permissionDescription, permissionLabel } = useI18n();
  const [name, setName] = useState(initialRole?.name ?? "");
  const [permissionIds, setPermissionIds] = useState(
    initialRole?.permissions.map((permission) => permission.id) ?? [],
  );

  function togglePermission(permissionId: string) {
    setPermissionIds((current) => current.includes(permissionId)
      ? current.filter((id) => id !== permissionId)
      : [...current, permissionId]);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({ name: name.trim(), permission_ids: permissionIds });
  }

  return (
    <form className="space-y-6" onSubmit={(event) => void handleSubmit(event)}>
      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="role-name"><T>Role name</T></label>
        <input className="crm-input w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950" id="role-name" maxLength={100} minLength={1} onChange={(event) => setName(event.target.value)} required value={name} />
      </div>

      <fieldset>
        <legend className="text-sm font-medium text-slate-800 dark:text-slate-100"><T>Permissions</T></legend>
        <p className="mt-1 text-sm text-slate-500"><T>Select the actions members with this role may perform.</T></p>
        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          {permissions.map((permission) => (
            <label className="flex items-start gap-3 rounded-lg border border-slate-200 p-3 text-sm dark:border-slate-800" key={permission.id}>
              <input checked={permissionIds.includes(permission.id)} className="mt-0.5 h-4 w-4 shrink-0 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 dark:border-slate-700" onChange={() => togglePermission(permission.id)} type="checkbox" />
              <span><span className="block font-medium text-slate-800 dark:text-slate-100">{permissionLabel(permission.name)}</span>{permission.description ? <span className="mt-1 block text-xs leading-5 text-slate-500">{permissionDescription(permission.name)}</span> : null}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        {onCancel ? <Button disabled={isSubmitting} onClick={onCancel} variant="tertiary"><T>Cancel</T></Button> : null}
        <Button disabled={isSubmitting} type="submit">{isSubmitting ? <T>Saving...</T> : <T>{submitLabel}</T>}</Button>
      </div>
    </form>
  );
}
