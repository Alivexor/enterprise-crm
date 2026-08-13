import { T } from "@/components/i18n/i18n-provider";
import Link from "next/link";

import { EmptyState } from "@/components/ui/page-state";
import { RecordMark } from "@/components/ui/record-mark";
import type { Contact } from "@/types/contact";

type ContactListProps = {
  companyNames: ReadonlyMap<string, string>;
  contacts: Contact[];
};

export function ContactList({ companyNames, contacts }: ContactListProps) {
  if (contacts.length === 0) {
    return <EmptyState description="Add a contact to start tracking the people at your customer companies." title="No contacts yet" />;
  }

  return (
    <div className="crm-table-shell overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
      <div className="grid grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)] gap-4 border-b border-slate-200 px-5 py-3 text-xs font-semibold tracking-wide text-slate-500 uppercase dark:border-slate-800 sm:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,1fr)]">
        <span><T>Contact</T></span>
        <span><T>Company</T></span>
        <span className="hidden sm:block"><T>Email</T></span>
      </div>
      <ul className="divide-y divide-slate-100 dark:divide-slate-800">
        {contacts.map((contact) => (
          <li key={contact.id}>
            <Link
              className="grid grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)] items-center gap-4 px-5 py-4 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-inset focus-visible:ring-indigo-500 dark:hover:bg-slate-900/60 sm:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_minmax(0,1fr)]"
              href={`/dashboard/contacts/${contact.id}`}
            >
              <span className="flex min-w-0 items-center gap-3">
                <RecordMark label={`${contact.first_name} ${contact.last_name}`} tone="cyan" />
                <span className="min-w-0">
                  <span className="block truncate text-sm font-bold tracking-[-.01em] text-slate-900 dark:text-white">{contact.first_name} {contact.last_name}</span>
                  <span className="mt-1 block truncate text-xs text-slate-500 sm:hidden">{contact.email ?? contact.phone ?? <T>No contact details</T>}</span>
                </span>
              </span>
              <span className="truncate text-sm text-slate-600 dark:text-slate-300">
                {companyNames.get(contact.company_id) ?? <T>Unknown company</T>}
              </span>
              <span className="hidden truncate text-sm text-indigo-600 dark:text-indigo-300 sm:block">
                {contact.email ?? "—"}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
