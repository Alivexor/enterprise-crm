"use client";

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { LocalizedDateTime, LocalizedEnum } from "@/components/i18n/localized-value";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/page-state";
import { PaginationControls } from "@/components/ui/pagination-controls";
import { useToast } from "@/components/ui/toast-provider";
import { usePaginatedResource } from "@/hooks/use-paginated-resource";
import { ApiError } from "@/services/api-client";
import { notificationService } from "@/services/notification-service";
import type { Notification, NotificationReadState } from "@/types/notification";
import { announceNotificationsChanged } from "@/utils/notification-events";

const filters: Array<{ label: string; value: NotificationReadState }> = [
  { label: "All", value: "all" },
  { label: "Unread", value: "unread" },
  { label: "Read", value: "read" },
];

function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to update notifications.";
}

function entityHref(notification: Notification): string | null {
  if (!notification.entity_id || !notification.entity_type) return null;
  const routes: Record<string, string> = {
    activity: "activities", company: "companies", contact: "contacts", deal: "deals",
    lead: "leads", note: "notes", task: "tasks",
  };
  const route = routes[notification.entity_type];
  return route ? `/dashboard/${route}/${notification.entity_id}` : null;
}

function InboxGlyph() {
  return (
    <svg aria-hidden="true" className="h-5 w-5" fill="none" viewBox="0 0 24 24">
      <path d="M5.2 7.2 7.4 4.8h9.2l2.2 2.4v10.6a1.8 1.8 0 0 1-1.8 1.8H7a1.8 1.8 0 0 1-1.8-1.8V7.2Z" stroke="currentColor" strokeLinejoin="round" strokeWidth="1.7" />
      <path d="M5.4 14h4l1.2 1.8h2.8l1.2-1.8h4" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.7" />
    </svg>
  );
}

export function NotificationsWorkspace() {
  const { enumLabel, formatNumber, locale, t } = useI18n();
  const { notify } = useToast();
  const [readState, setReadState] = useState<NotificationReadState>("all");
  const [page, setPage] = useState(1);
  const [isMarkingAllRead, setIsMarkingAllRead] = useState(false);
  const [isMarkingBulk, setIsMarkingBulk] = useState(false);
  const [markingId, setMarkingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(() => new Set());

  const loadNotifications = useCallback(
    () => notificationService.list({ page, page_size: 25, read: readState }),
    [page, readState],
  );
  const { error, isLoading, items, meta, reload } = usePaginatedResource(loadNotifications);
  const unreadIds = useMemo(() => items.filter((item) => item.read_at === null).map((item) => item.id), [items]);
  const allVisibleUnreadSelected = unreadIds.length > 0 && unreadIds.every((id) => selectedIds.has(id));

  function refreshAfterMutation(nextPage?: number) {
    setSelectedIds(new Set());
    announceNotificationsChanged();
    if (nextPage !== undefined && nextPage !== page) setPage(nextPage);
    else reload();
  }

  async function markRead(notificationId: string) {
    setMarkingId(notificationId);
    setActionError(null);
    try {
      await notificationService.markRead(notificationId);
      notify({ title: t("Notification marked as read"), tone: "success" });
      const nextPage = readState === "unread" && items.length === 1 && page > 1 ? page - 1 : undefined;
      refreshAfterMutation(nextPage);
    } catch (caughtError) {
      const message = t(getErrorMessage(caughtError));
      setActionError(message);
      notify({ description: message, title: t("Notification update failed"), tone: "error" });
    } finally {
      setMarkingId(null);
    }
  }

  async function markSelectedRead() {
    const ids = [...selectedIds];
    if (!ids.length) return;
    setIsMarkingBulk(true);
    setActionError(null);
    try {
      const result = await notificationService.markBulkRead(ids);
      notify({
        description: t("Selected notifications are now cleared from the unread queue."),
        title: t("{count} notifications marked as read", { count: formatNumber(result.updated) }),
        tone: "success",
      });
      const nextPage = readState === "unread" && ids.length >= items.length && page > 1 ? page - 1 : undefined;
      refreshAfterMutation(nextPage);
    } catch (caughtError) {
      const message = t(getErrorMessage(caughtError));
      setActionError(message);
      notify({ description: message, title: t("Notification update failed"), tone: "error" });
    } finally {
      setIsMarkingBulk(false);
    }
  }

  async function markAllRead() {
    setIsMarkingAllRead(true);
    setActionError(null);
    try {
      await notificationService.markAllRead();
      notify({
        description: t("Your inbox has no unread notifications remaining."),
        title: t("Inbox cleared"),
        tone: "success",
      });
      refreshAfterMutation(1);
    } catch (caughtError) {
      const message = t(getErrorMessage(caughtError));
      setActionError(message);
      notify({ description: message, title: t("Notification update failed"), tone: "error" });
    } finally {
      setIsMarkingAllRead(false);
    }
  }

  function toggleSelection(notificationId: string) {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (next.has(notificationId)) next.delete(notificationId);
      else next.add(notificationId);
      return next;
    });
  }

  function toggleVisibleUnread() {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (allVisibleUnreadSelected) unreadIds.forEach((id) => next.delete(id));
      else unreadIds.forEach((id) => next.add(id));
      return next;
    });
  }

  return (
    <section className="crm-page mx-auto max-w-6xl">
      <div className="crm-hero px-6 py-7 sm:px-8 sm:py-8">
        <div className="relative z-[1] flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl">
            <p className="crm-kicker"><T>Workspace</T></p>
            <div className="mt-4 flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-600 ring-1 ring-inset ring-indigo-500/15 dark:bg-indigo-500/15 dark:text-indigo-300">
                <InboxGlyph />
              </span>
              <h1 className="crm-title"><T>Inbox</T></h1>
            </div>
            <p className="crm-subtitle mt-3 max-w-2xl"><T>Stay current on records and work assigned to you.</T></p>
          </div>
          {readState !== "read" ? (
            <Button disabled={meta.total === 0 || isMarkingAllRead} onClick={() => void markAllRead()} variant="secondary">
              {isMarkingAllRead ? <T>Marking...</T> : <T>Mark all as read</T>}
            </Button>
          ) : null}
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div className="crm-inbox-stat"><p className="text-[10px] font-bold uppercase tracking-[.12em] text-slate-400"><T>Items in this view</T></p><p className="mt-2 text-2xl font-black tracking-[-.04em] text-slate-950 dark:text-white">{formatNumber(meta.total)}</p></div>
        <div className="crm-inbox-stat"><p className="text-[10px] font-bold uppercase tracking-[.12em] text-slate-400"><T>Unread in view</T></p><p className="mt-2 text-2xl font-black tracking-[-.04em] text-indigo-600 dark:text-indigo-300">{formatNumber(unreadIds.length)}</p></div>
        <div className="crm-inbox-stat"><p className="text-[10px] font-bold uppercase tracking-[.12em] text-slate-400"><T>Selected</T></p><p className="mt-2 text-2xl font-black tracking-[-.04em] text-slate-950 dark:text-white">{formatNumber(selectedIds.size)}</p></div>
      </div>

      <div className="crm-toolbar mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-2" role="group" aria-label={t("Notification filters")}>
          {filters.map((filter) => (
            <Button
              aria-pressed={readState === filter.value}
              key={filter.value}
              onClick={() => { setPage(1); setReadState(filter.value); setSelectedIds(new Set()); setActionError(null); }}
              size="sm"
              variant={readState === filter.value ? "primary" : "tertiary"}
            >
              <T>{filter.label}</T>
            </Button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {unreadIds.length > 0 ? (
            <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl px-3 py-2 text-xs font-bold text-slate-600 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800">
              <input checked={allVisibleUnreadSelected} className="h-4 w-4 accent-indigo-600" onChange={toggleVisibleUnread} type="checkbox" />
              <T>Select visible unread</T>
            </label>
          ) : null}
          {selectedIds.size > 0 ? (
            <Button disabled={isMarkingBulk} onClick={() => void markSelectedRead()} size="sm" variant="secondary">
              {isMarkingBulk ? <T>Marking...</T> : <>{t("Mark selected read")} ({formatNumber(selectedIds.size)})</>}
            </Button>
          ) : null}
        </div>
      </div>

      {actionError ? (
        <div className="crm-inline-feedback mt-4" role="alert">
          <span aria-hidden="true" className="mt-1 h-2 w-2 shrink-0 rounded-full bg-rose-500" />
          <p>{actionError}</p>
        </div>
      ) : null}

      <div className="mt-4">
        {isLoading ? <LoadingState label="Loading notifications..." /> : null}
        {!isLoading && error ? <ErrorState action={<Button onClick={reload}><T>Try again</T></Button>} description={error} title="Unable to load notifications" /> : null}
        {!isLoading && !error && items.length === 0 ? <EmptyState description="New assignments and CRM updates will appear here." title={readState === "unread" ? "No unread notifications" : "No notifications yet"} /> : null}
        {!isLoading && !error && items.length > 0 ? (
          <ul className="space-y-2.5">
            {items.map((notification) => {
              const href = entityHref(notification);
              const isUnread = notification.read_at === null;
              const content = (
                <div className="flex min-w-0 items-start gap-3">
                  <span aria-hidden="true" className={isUnread ? "mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full bg-indigo-500 shadow-[0_0_0_4px_rgba(99,102,241,.12)]" : "mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full bg-slate-300 dark:bg-slate-600"} />
                  <div className="min-w-0">
                    <p className="font-bold tracking-[-.01em] text-slate-900 dark:text-white">{locale === "fa" && notification.type.endsWith("_assigned") ? `${enumLabel(notification.entity_type ?? notification.type.replace("_assigned", ""))} به شما اختصاص داده شد` : notification.title}</p>
                    {notification.body ? <p className="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">{notification.body}</p> : null}
                    <p className="mt-2 text-xs text-slate-500"><LocalizedEnum value={notification.type} /> · <LocalizedDateTime value={notification.created_at} /></p>
                  </div>
                </div>
              );
              return (
                <li className="crm-inbox-item" data-unread={isUnread ? "true" : "false"} key={notification.id}>
                  <div className="flex flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:px-5">
                    {isUnread ? <input aria-label={t("Select notification")} checked={selectedIds.has(notification.id)} className="h-4 w-4 shrink-0 accent-indigo-600" onChange={() => toggleSelection(notification.id)} type="checkbox" /> : <span className="hidden h-4 w-4 shrink-0 sm:block" />}
                    {href ? <Link className="min-w-0 flex-1 rounded-xl focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-200 dark:focus-visible:ring-indigo-950" href={href}>{content}</Link> : <div className="min-w-0 flex-1">{content}</div>}
                    <div className="flex shrink-0 flex-wrap gap-2 sm:ps-2">
                      {href ? <Link className="inline-flex min-h-9 items-center justify-center rounded-xl px-3.5 py-2 text-sm font-bold text-indigo-700 transition hover:bg-indigo-100 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-200 dark:text-indigo-200 dark:hover:bg-indigo-950 dark:focus-visible:ring-indigo-950" href={href}><T>Open</T></Link> : null}
                      {isUnread ? <Button disabled={markingId === notification.id} onClick={() => void markRead(notification.id)} size="sm" variant="secondary">{markingId === notification.id ? <T>Marking...</T> : <T>Mark read</T>}</Button> : null}
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        ) : null}
        {!error ? <PaginationControls isLoading={isLoading} meta={meta} onPageChange={(nextPage) => { setSelectedIds(new Set()); setActionError(null); setPage(nextPage); }} /> : null}
      </div>
    </section>
  );
}
