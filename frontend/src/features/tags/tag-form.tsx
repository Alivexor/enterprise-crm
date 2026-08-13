"use client";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import type { TagInput } from "@/types/tag";

type TagFormProps = {
  initialValues?: TagInput;
  isSubmitting: boolean;
  onCancel?: () => void;
  onSubmit: (values: TagInput) => Promise<void>;
  submitLabel: string;
};

const initialTag: TagInput = { color: "#4f46e5", name: "" };

const inputClassName =
  "w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-950 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:ring-indigo-950";

export function TagForm({
  initialValues = initialTag,
  isSubmitting,
  onCancel,
  onSubmit,
  submitLabel,
}: TagFormProps) {
  const { t } = useI18n();
  const [name, setName] = useState(initialValues.name);
  const [color, setColor] = useState(initialValues.color);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit({ color, name: name.trim() });
  }

  return (
    <form className="space-y-5" onSubmit={(event) => void handleSubmit(event)}>
      <div className="grid gap-5 sm:grid-cols-[1fr_auto]">
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="tag-name"><T>Name</T></label>
          <input className={inputClassName} id="tag-name" maxLength={100} minLength={1} onChange={(event) => setName(event.target.value)} required value={name} />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-800 dark:text-slate-100" htmlFor="tag-color"><T>Color</T></label>
          <input aria-label={t("Tag color")} className="crm-input h-11 w-full cursor-pointer rounded-lg border border-slate-300 bg-white p-1 dark:border-slate-700 dark:bg-slate-950 sm:w-16" id="tag-color" onChange={(event) => setColor(event.target.value)} type="color" value={color} />
        </div>
      </div>
      <div className="flex flex-col-reverse gap-3 pt-1 sm:flex-row sm:justify-end">
        {onCancel ? <Button disabled={isSubmitting} onClick={onCancel} variant="tertiary"><T>Cancel</T></Button> : null}
        <Button disabled={isSubmitting} type="submit">{isSubmitting ? <T>Saving...</T> : <T>{submitLabel}</T>}</Button>
      </div>
    </form>
  );
}
