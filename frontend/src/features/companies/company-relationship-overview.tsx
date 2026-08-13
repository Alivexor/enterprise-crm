"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, type ReactNode } from "react";

import { T, useI18n } from "@/components/i18n/i18n-provider";
import { LocalizedDateTime, LocalizedEnum } from "@/components/i18n/localized-value";
import { StatusBadge } from "@/components/ui/status-badge";
import { useAuth } from "@/hooks/use-auth";
import { activityService } from "@/services/activity-service";
import { contactService } from "@/services/contact-service";
import { dealService } from "@/services/deal-service";
import { noteService } from "@/services/note-service";
import type { Activity } from "@/types/activity";
import type { Contact } from "@/types/contact";
import type { Deal } from "@/types/deal";
import type { Note } from "@/types/note";

type CompanyRelationshipOverviewProps = { companyId: string };

type LoadState = {
  activities: Activity[];
  activitiesTotal: number;
  contacts: Contact[];
  contactsTotal: number;
  deals: Deal[];
  dealsTotal: number;
  notes: Note[];
  notesTotal: number;
};

const emptyState: LoadState = {
  activities: [], activitiesTotal: 0,
  contacts: [], contactsTotal: 0,
  deals: [], dealsTotal: 0,
  notes: [], notesTotal: 0,
};

export function CompanyRelationshipOverview({ companyId }: CompanyRelationshipOverviewProps) {
  const { user } = useAuth();
  const { formatNumber, formatMoney, isRtl, t } = useI18n();
  const permissions = useMemo(
    () => new Set(user?.permissions.map((permission) => permission.name) ?? []),
    [user],
  );
  const [data, setData] = useState<LoadState>(emptyState);
  const [isLoading, setIsLoading] = useState(true);
  const [partialFailure, setPartialFailure] = useState(false);

  useEffect(() => {
    let active = true;
    const jobs: Array<Promise<void>> = [];
    const next: LoadState = { ...emptyState };
    let failed = false;

    if (permissions.has("contacts.read")) {
      jobs.push(contactService.list({ company_id: companyId, page: 1, page_size: 6, sort_by: "last_name", sort_direction: "asc" }).then((response) => {
        next.contacts = response.items;
        next.contactsTotal = response.meta.total;
      }).catch(() => { failed = true; }));
    }
    if (permissions.has("deals.read")) {
      jobs.push(dealService.list({ company_id: companyId, page: 1, page_size: 6, sort_by: "updated_at", sort_direction: "desc" }).then((response) => {
        next.deals = response.items;
        next.dealsTotal = response.meta.total;
      }).catch(() => { failed = true; }));
    }
    if (permissions.has("notes.read")) {
      jobs.push(noteService.list({ company_id: companyId, page: 1, page_size: 5, sort_by: "updated_at", sort_direction: "desc" }).then((response) => {
        next.notes = response.items;
        next.notesTotal = response.meta.total;
      }).catch(() => { failed = true; }));
    }
    if (permissions.has("activities.read")) {
      jobs.push(activityService.list({ company_id: companyId, completed: false, page: 1, page_size: 5, sort_by: "due_date", sort_direction: "asc" }).then((response) => {
        next.activities = response.items;
        next.activitiesTotal = response.meta.total;
      }).catch(() => { failed = true; }));
    }

    Promise.all(jobs).then(() => {
      if (!active) return;
      setData(next);
      setPartialFailure(failed);
      setIsLoading(false);
    });

    return () => { active = false; };
  }, [companyId, permissions]);

  const openDeals = data.deals.filter((deal) => deal.status === "open");
  const visibleOpenValue = openDeals.reduce((total, deal) => total + Number(deal.value), 0);
  const primaryCurrency = openDeals[0]?.currency ?? data.deals[0]?.currency ?? "USD";
  const timeline = useMemo(() => [
    ...data.activities.map((activity) => ({
      date: activity.created_at,
      href: `/dashboard/activities/${activity.id}`,
      id: `activity-${activity.id}`,
      kind: "activity" as const,
      meta: activity.type,
      text: activity.title,
    })),
    ...data.notes.map((note) => ({
      date: note.updated_at,
      href: `/dashboard/notes/${note.id}`,
      id: `note-${note.id}`,
      kind: "note" as const,
      meta: "note",
      text: note.content,
    })),
  ].sort((left, right) => new Date(right.date).getTime() - new Date(left.date).getTime()).slice(0, 8), [data.activities, data.notes]);

  if (isLoading) {
    return (
      <div className="mt-6 grid gap-3 sm:grid-cols-4">
        {[0, 1, 2, 3].map((item) => <div className="h-24 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-900" key={item} />)}
      </div>
    );
  }

  const hasAnyPermission = ["contacts.read", "deals.read", "notes.read", "activities.read"].some((permission) => permissions.has(permission));
  if (!hasAnyPermission) return null;

  return (
    <section className="mt-7 border-t border-slate-100 pt-7 dark:border-slate-800">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="crm-kicker"><T>Customer 360</T></p>
          <h2 className="mt-3 text-xl font-bold tracking-[-.025em] text-slate-950 dark:text-white"><T>Relationship overview</T></h2>
          <p className="mt-2 text-sm leading-6 text-slate-500"><T>Sales context, people, notes and follow-ups around this account.</T></p>
        </div>
        {partialFailure ? <span className="text-xs font-medium text-amber-600 dark:text-amber-300"><T>Some relationship data is temporarily unavailable.</T></span> : null}
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {permissions.has("contacts.read") ? <Metric label="Contacts" value={formatNumber(data.contactsTotal)} /> : null}
        {permissions.has("deals.read") ? <Metric label="Deals" value={formatNumber(data.dealsTotal)} /> : null}
        {permissions.has("notes.read") ? <Metric label="Notes" value={formatNumber(data.notesTotal)} /> : null}
        {permissions.has("activities.read") ? <Metric label="Upcoming activities" value={formatNumber(data.activitiesTotal)} /> : null}
      </div>

      {permissions.has("deals.read") && data.deals.length > 0 ? (
        <div className="mt-4 rounded-2xl border border-indigo-100/80 bg-gradient-to-r from-indigo-50/80 to-cyan-50/50 px-4 py-3.5 shadow-sm dark:border-indigo-950 dark:from-indigo-950/30 dark:to-cyan-950/15">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-100"><T>Visible open pipeline</T></p>
            <p className="text-sm font-bold text-indigo-700 dark:text-indigo-200">{formatMoney(visibleOpenValue, primaryCurrency)}</p>
          </div>
        </div>
      ) : null}

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        {permissions.has("contacts.read") ? (
          <RelationshipCard title="Key contacts" href="/dashboard/contacts" linkLabel="View contacts">
            {data.contacts.length === 0 ? <EmptyLine text="No contacts linked to this company yet." /> : data.contacts.slice(0, 4).map((contact) => (
              <Link className="group flex items-center justify-between gap-3 rounded-xl px-2.5 py-2.5 transition hover:bg-indigo-50/55 dark:hover:bg-indigo-950/20" href={`/dashboard/contacts/${contact.id}`} key={contact.id}>
                <span className="min-w-0"><span className="block truncate text-sm font-bold tracking-[-.01em] text-slate-900 dark:text-white">{contact.first_name} {contact.last_name}</span><span className="mt-0.5 block truncate text-xs text-slate-500" dir="ltr">{contact.email ?? contact.phone ?? t("No contact details")}</span></span>
                <span className="text-xs text-indigo-500">{isRtl ? "←" : "→"}</span>
              </Link>
            ))}
          </RelationshipCard>
        ) : null}

        {permissions.has("deals.read") ? (
          <RelationshipCard title="Recent deals" href="/dashboard/deals" linkLabel="View deals">
            {data.deals.length === 0 ? <EmptyLine text="No deals linked to this company yet." /> : data.deals.slice(0, 4).map((deal) => (
              <Link className="group flex items-center justify-between gap-3 rounded-xl px-2.5 py-2.5 transition hover:bg-indigo-50/55 dark:hover:bg-indigo-950/20" href={`/dashboard/deals/${deal.id}`} key={deal.id}>
                <span className="min-w-0"><span className="block truncate text-sm font-bold tracking-[-.01em] text-slate-900 dark:text-white">{deal.title}</span><span className="mt-0.5 block text-xs text-slate-500">{formatMoney(deal.value, deal.currency)}</span></span>
                <StatusBadge tone={deal.status === "won" ? "green" : deal.status === "lost" ? "red" : "blue"}><LocalizedEnum value={deal.status} /></StatusBadge>
              </Link>
            ))}
          </RelationshipCard>
        ) : null}

        {permissions.has("activities.read") ? (
          <RelationshipCard title="Upcoming activities" href="/dashboard/activities" linkLabel="View activities">
            {data.activities.length === 0 ? <EmptyLine text="No upcoming activity is scheduled for this company." /> : data.activities.slice(0, 4).map((activity) => (
              <Link className="group block rounded-xl px-2.5 py-2.5 transition hover:bg-indigo-50/55 dark:hover:bg-indigo-950/20" href={`/dashboard/activities/${activity.id}`} key={activity.id}>
                <div className="flex items-center justify-between gap-3"><span className="truncate text-sm font-bold tracking-[-.01em] text-slate-900 dark:text-white">{activity.title}</span><StatusBadge tone="violet"><LocalizedEnum value={activity.type} /></StatusBadge></div>
                <p className="mt-1 text-xs text-slate-500"><LocalizedDateTime value={activity.due_date} /></p>
              </Link>
            ))}
          </RelationshipCard>
        ) : null}

        {permissions.has("notes.read") ? (
          <RelationshipCard title="Recent notes" href="/dashboard/notes" linkLabel="View notes">
            {data.notes.length === 0 ? <EmptyLine text="No notes have been added for this company." /> : data.notes.slice(0, 3).map((note) => (
              <Link className="group block rounded-xl px-2.5 py-2.5 transition hover:bg-indigo-50/55 dark:hover:bg-indigo-950/20" href={`/dashboard/notes/${note.id}`} key={note.id}>
                <p className="line-clamp-2 text-sm leading-5 text-slate-800 dark:text-slate-100">{note.content}</p>
                <p className="mt-1 text-xs text-slate-500"><LocalizedDateTime value={note.updated_at} /></p>
              </Link>
            ))}
          </RelationshipCard>
        ) : null}
      </div>

      {(permissions.has("activities.read") || permissions.has("notes.read")) ? (
        <article className="crm-card mt-5 overflow-hidden">
          <div className="flex items-end justify-between gap-3 border-b border-slate-200/70 px-5 py-4 dark:border-slate-800">
            <div><h3 className="text-sm font-bold text-slate-950 dark:text-white"><T>Relationship timeline</T></h3><p className="mt-1 text-xs text-slate-500"><T>Recent notes and interactions around this customer account.</T></p></div>
            <span className="crm-chip text-xs">{formatNumber(timeline.length)} <T>events</T></span>
          </div>
          {timeline.length === 0 ? <div className="p-5"><EmptyLine text="No relationship activity has been recorded yet." /></div> : (
            <ol className="divide-y divide-slate-100 dark:divide-slate-800">
              {timeline.map((event) => (
                <li key={event.id}>
                  <Link className="group flex items-start gap-3 px-5 py-4 transition hover:bg-indigo-50/35 dark:hover:bg-indigo-950/10" href={event.href}>
                    <span className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${event.kind === "note" ? "bg-violet-50 text-violet-600 dark:bg-violet-950/40 dark:text-violet-300" : "bg-cyan-50 text-cyan-600 dark:bg-cyan-950/40 dark:text-cyan-300"}`}>
                      {event.kind === "note" ? <svg aria-hidden="true" className="h-4 w-4" fill="none" viewBox="0 0 20 20"><path d="M5 3.5h10a1.5 1.5 0 0 1 1.5 1.5v10a1.5 1.5 0 0 1-1.5 1.5H5A1.5 1.5 0 0 1 3.5 15V5A1.5 1.5 0 0 1 5 3.5Zm2.2 4h5.6M7.2 10h5.6M7.2 12.5h3.3" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" /></svg> : <svg aria-hidden="true" className="h-4 w-4" fill="none" viewBox="0 0 20 20"><path d="M4 10h3l2-5 3.5 10 2-5H17" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.6" /></svg>}
                    </span>
                    <span className="min-w-0 flex-1"><span className="line-clamp-2 text-sm font-semibold leading-5 text-slate-800 transition group-hover:text-indigo-700 dark:text-slate-100 dark:group-hover:text-indigo-200">{event.text}</span><span className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-slate-500"><LocalizedEnum value={event.meta} /><span>·</span><LocalizedDateTime value={event.date} /></span></span>
                    <svg aria-hidden="true" className="mt-2 h-4 w-4 shrink-0 text-slate-300 transition group-hover:text-indigo-400 rtl:rotate-180 dark:text-slate-700" fill="none" viewBox="0 0 20 20"><path d="m7 5 5 5-5 5" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.7" /></svg>
                  </Link>
                </li>
              ))}
            </ol>
          )}
        </article>
      ) : null}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="crm-metric px-4 py-3.5"><p className="text-xs font-semibold text-slate-500"><T>{label}</T></p><p className="mt-2 text-xl font-bold text-slate-950 dark:text-white">{value}</p></div>;
}

function RelationshipCard({ children, href, linkLabel, title }: { children: ReactNode; href: string; linkLabel: string; title: string }) {
  return <article className="crm-card crm-card-hover p-4"><div className="mb-2 flex items-center justify-between gap-3"><h3 className="text-sm font-bold text-slate-900 dark:text-white"><T>{title}</T></h3><Link className="text-xs font-semibold text-indigo-600 hover:text-indigo-500 dark:text-indigo-300" href={href}><T>{linkLabel}</T></Link></div><div className="space-y-1">{children}</div></article>;
}

function EmptyLine({ text }: { text: string }) {
  return <p className="px-2 py-4 text-sm text-slate-500"><T>{text}</T></p>;
}
