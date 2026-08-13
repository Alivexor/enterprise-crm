"use client";

import { useEffect, useMemo, useState } from "react";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast-provider";
import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/services/api-client";
import { v3Service } from "@/services/v3-service";
import type { CustomFieldDefinition } from "@/types/v3";

function message(error: unknown): string { return error instanceof ApiError ? error.message : "Unable to load custom fields."; }

export function CustomFieldsPanel({ entityType, entityId }: { entityType: "company" | "contact" | "lead" | "deal"; entityId: string }) {
  const { t } = useI18n();
  const { user } = useAuth();
  const { notify } = useToast();
  const permissions = useMemo(() => new Set(user?.permissions.map((item) => item.name) ?? []), [user]);
  const canRead = permissions.has("custom_fields.read");
  const canUpdate = permissions.has("custom_fields.update");
  const [definitions, setDefinitions] = useState<CustomFieldDefinition[]>([]);
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(canRead);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!canRead) return;
    let active = true;
    Promise.all([v3Service.customFields.list(entityType), v3Service.customFields.values(entityType, entityId)])
      .then(([defs, response]) => { if (active) { setDefinitions(defs.filter((item) => item.is_active)); setValues(response.values); } })
      .catch((cause) => { if (active) notify({ tone: "error", title: t("Unable to load custom fields"), description: t(message(cause)) }); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [canRead, entityId, entityType, notify, t]);

  if (!canRead) return null;
  if (loading) return <section className="rounded-2xl border border-slate-200/70 bg-slate-50/55 p-5 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900/45"><T>Loading custom fields…</T></section>;
  if (!definitions.length) return null;

  function setValue(key: string, value: unknown) { setValues((current) => ({ ...current, [key]: value })); }
  async function save() {
    setSaving(true);
    try { const response = await v3Service.customFields.saveValues(entityType, entityId, values); setValues(response.values); notify({ tone: "success", title: t("Custom fields saved") }); }
    catch (cause) { notify({ tone: "error", title: t("Unable to save custom fields"), description: t(message(cause)) }); }
    finally { setSaving(false); }
  }

  return <section className="rounded-2xl border border-slate-200/70 bg-slate-50/55 p-5 dark:border-slate-800 dark:bg-slate-900/45">
    <div className="flex items-start justify-between gap-4"><div><h2 className="text-sm font-black text-slate-950 dark:text-white"><T>Custom fields</T></h2><p className="mt-1 text-xs text-slate-500"><T>Workspace-defined fields for this record.</T></p></div>{canUpdate ? <Button disabled={saving} onClick={() => void save()} size="sm" variant="secondary">{saving ? t("Saving…") : t("Save custom fields")}</Button> : null}</div>
    <div className="mt-4 grid gap-4 sm:grid-cols-2">{definitions.map((definition) => {
      const raw = values[definition.field_key];
      const common = { disabled: !canUpdate, id: `custom-${definition.id}`, name: definition.field_key };
      return <label className="text-xs font-bold text-slate-600 dark:text-slate-300" key={definition.id}><span>{definition.label}{definition.required ? " *" : ""}</span>{definition.data_type === "boolean" ? <span className="mt-2 flex min-h-10 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 dark:border-slate-700 dark:bg-slate-950"><input checked={Boolean(raw)} onChange={(e) => setValue(definition.field_key, e.target.checked)} type="checkbox" {...common} /><T>{raw ? "Yes" : "No"}</T></span> : definition.data_type === "select" ? <select className="crm-select mt-2 w-full" onChange={(e) => setValue(definition.field_key, e.target.value || null)} value={String(raw ?? "")} {...common}><option value="">—</option>{(definition.options ?? []).map((option) => <option key={option} value={option}>{option}</option>)}</select> : definition.data_type === "multi_select" ? <select className="crm-select mt-2 min-h-24 w-full" multiple onChange={(e) => setValue(definition.field_key, Array.from(e.target.selectedOptions as HTMLCollectionOf<HTMLOptionElement>, (option) => option.value))} value={Array.isArray(raw) ? raw.map(String) : []} {...common}>{(definition.options ?? []).map((option) => <option key={option} value={option}>{option}</option>)}</select> : <input className="crm-input mt-2 w-full" onChange={(e) => setValue(definition.field_key, e.target.value || null)} type={definition.data_type === "date" ? "date" : definition.data_type === "number" || definition.data_type === "currency" ? "number" : definition.data_type === "email" ? "email" : definition.data_type === "url" ? "url" : "text"} value={raw === null || raw === undefined ? "" : String(raw)} {...common} />}</label>;
    })}</div>
  </section>;
}
