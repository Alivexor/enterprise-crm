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
import { TaskForm } from "@/features/tasks/task-form";
import { ApiError } from "@/services/api-client";
import { taskService } from "@/services/task-service";
import type { Task, TaskInput } from "@/types/task";

function getErrorMessage(error: unknown): string { return error instanceof ApiError ? error.message : "Unable to load this task."; }
function tone(status: Task["status"]): "blue" | "gray" | "green" | "orange" { return status === "completed" ? "green" : status === "cancelled" ? "gray" : status === "in_progress" ? "blue" : "orange"; }

export function TaskDetail({ taskId }: { taskId: string }) {
  const router = useRouter(); const [task, setTask] = useState<Task | null>(null); const [error, setError] = useState<string | null>(null); const [isEditing, setIsEditing] = useState(false); const [isLoading, setIsLoading] = useState(true); const [isSaving, setIsSaving] = useState(false); const [isDeleting, setIsDeleting] = useState(false);
  useEffect(() => { let isActive = true; async function loadTask() { try { const nextTask = await taskService.get(taskId); if (isActive) { setTask(nextTask); setError(null); } } catch (caughtError) { if (isActive) setError(getErrorMessage(caughtError)); } finally { if (isActive) setIsLoading(false); } } void loadTask(); return () => { isActive = false; }; }, [taskId]);
  async function updateTask(values: TaskInput) { setIsSaving(true); try { const nextTask = await taskService.update(taskId, values); setTask(nextTask); setError(null); setIsEditing(false); } catch (caughtError) { setError(getErrorMessage(caughtError)); } finally { setIsSaving(false); } }
  async function deleteTask() { if (!confirmDelete(task?.title)) return; setIsDeleting(true); try { await taskService.remove(taskId); router.replace("/dashboard/tasks"); } catch (caughtError) { setError(getErrorMessage(caughtError)); setIsDeleting(false); } }
  if (isLoading) return <LoadingState label="Loading task…" />;
  if (!task) return <section className="crm-page mx-auto max-w-4xl"><Link className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/tasks"><T>← Back to tasks</T></Link><div className="mt-6"><ErrorState description={error ?? "Task not found."} title="Unable to load task" /></div></section>;
  const initialValues: TaskInput = { description: task.description, due_date: task.due_date, priority: task.priority, status: task.status, title: task.title };
  return <section className="crm-page mx-auto max-w-4xl"><Link className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href="/dashboard/tasks"><T>← Back to tasks</T></Link><div className="crm-card mt-6 flex flex-col gap-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950 sm:p-7"><div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div><p className="crm-kicker"><T>Task</T></p><h1 className="crm-title mt-3">{task.title}</h1><div className="mt-3"><StatusBadge tone={tone(task.status)}><LocalizedEnum value={task.status} /></StatusBadge></div></div><div className="flex gap-2"><Button onClick={() => setIsEditing((value) => !value)} variant="secondary">{isEditing ? <T>Close edit</T> : <T>Edit</T>}</Button><Button disabled={isDeleting} onClick={() => void deleteTask()} variant="danger">{isDeleting ? <T>Deleting…</T> : <T>Delete</T>}</Button></div></div>{error ? <p className="rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:bg-rose-950/50 dark:text-rose-200" role="alert"><T>{error}</T></p> : null}{isEditing ? <TaskForm initialValues={initialValues} isSubmitting={isSaving} key={task.id} onCancel={() => setIsEditing(false)} onSubmit={updateTask} submitLabel="Save changes" /> : <dl className="grid gap-6 border-t border-slate-100 pt-6 sm:grid-cols-2 dark:border-slate-800"><div><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Priority</T></dt><dd className="mt-2 text-sm text-slate-800 dark:text-slate-100"><LocalizedEnum value={task.priority} /></dd></div><div><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Due date</T></dt><dd className="mt-2 text-sm text-slate-800 dark:text-slate-100"><LocalizedDateTime value={task.due_date} /></dd></div><div className="sm:col-span-2"><dt className="text-xs font-semibold tracking-wide text-slate-500 uppercase"><T>Description</T></dt><dd className="mt-2 whitespace-pre-wrap text-sm text-slate-800 dark:text-slate-100">{task.description ?? "—"}</dd></div></dl>}<AttachmentPanel entityId={task.id} entityType="task" /></div></section>;
}
