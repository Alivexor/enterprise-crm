"use client";

import { LocalizedDateTime, LocalizedEnum } from "@/components/i18n/localized-value";
import { T, confirmDelete } from "@/components/i18n/i18n-provider";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { AttachmentPanel } from "@/components/attachments/attachment-panel";
import { ErrorState, LoadingState } from "@/components/ui/page-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { ActivityForm } from "@/features/activities/activity-form";
import { ApiError } from "@/services/api-client";
import { activityService } from "@/services/activity-service";
import type { Activity, ActivityInput } from "@/types/activity";

function getErrorMessage(error: unknown): string { return error instanceof ApiError ? error.message : "Unable to load this activity."; }

export function ActivityDetail({ activityId }: { activityId: string }) {
  const router = useRouter(); const [activity, setActivity] = useState<Activity | null>(null); const [error, setError] = useState<string | null>(null); const [isEditing, setIsEditing] = useState(false); const [isLoading, setIsLoading] = useState(true); const [isSaving, setIsSaving] = useState(false); const [isDeleting, setIsDeleting] = useState(false);
  useEffect(() => { let isActive = true; async function loadActivity() { try { const nextActivity = await activityService.get(activityId); if (isActive) { setActivity(nextActivity); setError(null); } } catch (caughtError) { if (isActive) setError(getErrorMessage(caughtError)); } finally { if (isActive) setIsLoading(false); } } void loadActivity(); return () => { isActive = false; }; }, [activityId]);
  async function updateActivity(values: ActivityInput) { setIsSaving(true); try { const nextActivity = await activityService.update(activityId, values); setActivity(nextActivity); setError(null); setIsEditing(false); } catch (caughtError) { setError(getErrorMessage(caughtError)); } finally { setIsSaving(false); } }
  async function deleteActivity() { if (!confirmDelete(activity?.title)) return; setIsDeleting(true); try { await activityService.remove(activityId); router.replace("/dashboard/activities"); } catch (caughtError) { setError(getErrorMessage(caughtError)); setIsDeleting(false); } }
  if (isLoading) return <LoadingState label="Loading activity…" />;
  if (!activity) return <section className="crm-page mx-auto max-w-4xl"><Link className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/activities"><T>← Back to activities</T></Link><div className="mt-6"><ErrorState description={error ?? "Activity not found."} title="Unable to load activity" /></div></section>;
  const initialValues: ActivityInput = { company_id: activity.company_id, completed: activity.completed, contact_id: activity.contact_id, description: activity.description, due_date: activity.due_date, lead_id: activity.lead_id, title: activity.title, type: activity.type };
  return <section className="crm-page mx-auto max-w-4xl"><Link className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/activities"><T>← Back to activities</T></Link><div className="crm-card mt-6 flex flex-col gap-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-7"><div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div><p className="crm-kicker"><LocalizedEnum value={activity.type} /></p><h1 className="crm-title mt-3">{activity.title}</h1><div className="mt-3"><StatusBadge tone={activity.completed ? "green" : "orange"}>{activity.completed ? <T>Completed</T> : <T>Open</T>}</StatusBadge></div></div><div className="flex gap-2"><Button onClick={() => setIsEditing((value) => !value)} variant="secondary">{isEditing ? <T>Close edit</T> : <T>Edit</T>}</Button><Button disabled={isDeleting} onClick={() => void deleteActivity()} variant="danger">{isDeleting ? <T>Deleting…</T> : <T>Delete</T>}</Button></div></div>{error ? <p className="rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:bg-rose-950/50 dark:text-rose-200" role="alert"><T>{error}</T></p> : null}{isEditing ? <ActivityForm initialValues={initialValues} isSubmitting={isSaving} key={activity.id} onCancel={() => setIsEditing(false)} onSubmit={updateActivity} submitLabel="Save changes" /> : <dl className="grid gap-6 border-t border-slate-100 pt-6 sm:grid-cols-2 dark:border-slate-800"><div><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Due date</T></dt><dd className="mt-2 text-sm text-slate-800 dark:text-slate-100"><LocalizedDateTime value={activity.due_date} /></dd></div><div><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Created</T></dt><dd className="mt-2 text-sm text-slate-800 dark:text-slate-100"><LocalizedDateTime value={activity.created_at} /></dd></div><div className="sm:col-span-2"><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Description</T></dt><dd className="mt-2 whitespace-pre-wrap text-sm text-slate-800 dark:text-slate-100">{activity.description ?? "—"}</dd></div></dl>}<AttachmentPanel entityId={activity.id} entityType="activity" /></div></section>;
}
