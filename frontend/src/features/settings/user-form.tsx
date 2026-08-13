"use client";

import { T } from "@/components/i18n/i18n-provider";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import type { Role } from "@/types/role";
import type { ManagedUser, ManagedUserCreate, ManagedUserUpdate } from "@/types/user-management";

type UserFormProps = {
  initialUser?: ManagedUser;
  isSubmitting: boolean;
  mode: "create" | "edit";
  onCancel?: () => void;
  onSubmit: (values: ManagedUserCreate | ManagedUserUpdate) => Promise<void>;
  roles: Role[];
};

const inputClassName =
  "w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950";

export function UserForm({
  initialUser,
  isSubmitting,
  mode,
  onCancel,
  onSubmit,
  roles,
}: UserFormProps) {
  const [email, setEmail] = useState(initialUser?.email ?? "");
  const [firstName, setFirstName] = useState(initialUser?.first_name ?? "");
  const [lastName, setLastName] = useState(initialUser?.last_name ?? "");
  const [password, setPassword] = useState("");
  const [isActive, setIsActive] = useState(initialUser?.is_active ?? true);
  const [roleIds, setRoleIds] = useState(initialUser?.roles.map((role) => role.id) ?? []);

  function toggleRole(roleId: string) {
    setRoleIds((current) => current.includes(roleId)
      ? current.filter((id) => id !== roleId)
      : [...current, roleId]);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (mode === "create") {
      await onSubmit({
        email: email.trim(),
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        password,
        role_ids: roleIds,
      });
      return;
    }

    await onSubmit({
      email: email.trim(),
      first_name: firstName.trim(),
      is_active: isActive,
      last_name: lastName.trim(),
      role_ids: roleIds,
    });
  }

  return (
    <form className="space-y-6" onSubmit={(event) => void handleSubmit(event)}>
      <div className="grid gap-5 sm:grid-cols-2">
        <div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor={`${mode}-user-first-name`}><T>First name</T></label><input className={inputClassName} id={`${mode}-user-first-name`} maxLength={100} minLength={1} onChange={(event) => setFirstName(event.target.value)} required value={firstName} /></div>
        <div className="space-y-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor={`${mode}-user-last-name`}><T>Last name</T></label><input className={inputClassName} id={`${mode}-user-last-name`} maxLength={100} minLength={1} onChange={(event) => setLastName(event.target.value)} required value={lastName} /></div>
        <div className="space-y-2 sm:col-span-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor={`${mode}-user-email`}><T>Email address</T></label><input className={inputClassName} id={`${mode}-user-email`} maxLength={255} onChange={(event) => setEmail(event.target.value)} required type="email" value={email} /></div>
        {mode === "create" ? <div className="space-y-2 sm:col-span-2"><label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="create-user-password"><T>Temporary password</T></label><input autoComplete="new-password" className={inputClassName} id="create-user-password" minLength={12} onChange={(event) => setPassword(event.target.value)} required type="password" value={password} /><p className="text-xs text-slate-500"><T>Must contain at least 12 characters.</T></p></div> : null}
      </div>

      {mode === "edit" ? <label className="flex items-center gap-3 text-sm font-medium text-slate-800 dark:text-slate-100"><input checked={isActive} className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 dark:border-slate-700" onChange={(event) => setIsActive(event.target.checked)} type="checkbox" /><T>Active user</T></label> : null}

      <fieldset>
        <legend className="text-sm font-medium text-slate-800 dark:text-slate-100"><T>Roles</T></legend>
        <p className="mt-1 text-sm text-slate-500"><T>Choose at least one role for this user.</T></p>
        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          {roles.map((role) => <label className="flex items-center gap-3 rounded-lg border border-slate-200 p-3 text-sm text-slate-700 dark:border-slate-800 dark:text-slate-200" key={role.id}><input checked={roleIds.includes(role.id)} className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 dark:border-slate-700" onChange={() => toggleRole(role.id)} type="checkbox" />{role.name}</label>)}
        </div>
      </fieldset>

      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        {onCancel ? <Button disabled={isSubmitting} onClick={onCancel} variant="tertiary"><T>Cancel</T></Button> : null}
        <Button disabled={isSubmitting || roleIds.length === 0} type="submit">{isSubmitting ? <T>Saving...</T> : mode === "create" ? <T>Create user</T> : <T>Save changes</T>}</Button>
      </div>
    </form>
  );
}
